from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam
    )

class locustContainer(core.Construct):

    def __init__(self, scope: core.Construct, id: str, vpc, ecs_cluster, role, target_url: str, number_of_tasks = 1, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        name = id
        step = True

        task_def = ecs.Ec2TaskDefinition(self, name,
                                         network_mode=ecs.NetworkMode.AWS_VPC
                                        )

        container_env = {"TARGET_URL": target_url,
                         "LOCUST_MODE": role
                        }
        if role == "slave":
            container_env["LOCUST_MASTER_HOST"] = "master.loadgen"
        if step:
            container_env["LOCUST_OPTS"] = "--step-load"

        locust_container = task_def.add_container(
            name + "container",
            # Create an image we using the dockerfile in ./locust
            image=ecs.ContainerImage.from_asset("locust"),
            memory_reservation_mib=512,
            essential=True,
            logging=ecs.LogDrivers.aws_logs(stream_prefix=name),
            environment=container_env
        )

        locust_container.add_ulimits(
            ecs.Ulimit(
                name=ecs.UlimitName.NOFILE,
                soft_limit=65536,
                hard_limit=65536
            )
        )

        web_port_mapping = ecs.PortMapping(container_port=8089)
        if role != "standalone":
            slave1_port_mapping = ecs.PortMapping(container_port=5557)
            slave2_port_mapping = ecs.PortMapping(container_port=5558)
            locust_container.add_port_mappings(web_port_mapping,
                                               slave1_port_mapping,
                                               slave2_port_mapping
                                              )
        else:
            locust_container.add_port_mappings(web_port_mapping)


        security_group=ec2.SecurityGroup(
            self, "Locust",
            vpc=vpc,
            allow_all_outbound=True
        )

        security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(8089)
        )

        if role != "standalone":
            security_group.add_ingress_rule(
                ec2.Peer.any_ipv4(),
                ec2.Port.tcp(5557)
            )
            security_group.add_ingress_rule(
                ec2.Peer.any_ipv4(),
                ec2.Port.tcp(5558)
            )

        # Create the ecs service
        locust_service = ecs.Ec2Service(
            self, name +"service",
            cluster=ecs_cluster,
            task_definition=task_def,
            security_group=security_group,
            desired_count=number_of_tasks
        )

        locust_service.enable_cloud_map(name=role)

        # Create the ALB to present the Locust UI
        if role != "slave":
            self.lb = elbv2.ApplicationLoadBalancer(self, "LoustLB", vpc=vpc,
                                                    internet_facing=True
                                                   )
            # Forward port 80 to port 8089
            listener = self.lb.add_listener("Listener", port=80)
            listener.add_targets("ECS1",
                                 port=8089,
                                 protocol=elbv2.ApplicationProtocol.HTTP,
                                 targets=[locust_service]
                                 )
            core.CfnOutput(
                self, "lburl",
                description="URL for ALB fronting locust master",
                value="http://{}".format(self.lb.load_balancer_dns_name)
            )