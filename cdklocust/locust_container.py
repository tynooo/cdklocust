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
        
        
        task_def = ecs.Ec2TaskDefinition(self, name,
            network_mode=ecs.NetworkMode.AWS_VPC
        )
        
        if role == "slave":
            locust_container = task_def.add_container(
                name + "container",
                # Use Locust image from DockerHub
                # Or not. we'll use an image we create using the dockerfile in ./locust
                image=ecs.ContainerImage.from_asset("locust"),
                memory_reservation_mib=512,
                essential=True,
                logging=ecs.LogDrivers.aws_logs(stream_prefix=name),
                environment={"TARGET_URL": target_url,
                    "LOCUST_MODE": role,
                    #Need to update to pull the name from Cloudmap
                    "LOCUST_MASTER": "master.loadgen"
                }
            )
        else:
            locust_container = task_def.add_container(
                name + "container",
                # Use Locust image from DockerHub
                # Or not. we'll use an image we create using the dockerfile in ./locust
                image=ecs.ContainerImage.from_asset("locust"),
                memory_reservation_mib=512,
                essential=True,
                logging=ecs.LogDrivers.aws_logs(stream_prefix=name),
                environment={"TARGET_URL": target_url,
                    "LOCUST_MODE": role
                }
            )
            
        
        
        web_port_mapping = ecs.PortMapping(container_port=8089)
        if role != "standalone":
            slave1_port_mapping = ecs.PortMapping(container_port=5557)
            slave2_port_mapping = ecs.PortMapping(container_port=5558)
            locust_container.add_port_mappings(web_port_mapping,slave1_port_mapping,slave2_port_mapping)
        else:
            locust_container.add_port_mappings(web_port_mapping)


        security_group = ec2.SecurityGroup(
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
            cluster = ecs_cluster,
            task_definition = task_def,
            security_group = security_group,
            desired_count = number_of_tasks
        )
        
        locust_service.enable_cloud_map(name=role)
        
        # Create the ALB to present the Locust UI 
        if role != "slave":
            lb = elbv2.ApplicationLoadBalancer(self, "LB", vpc=vpc, internet_facing=True)
            listener = lb.add_listener("Listener", port=80)
            listener.add_targets("ECS1",
                port=80,
                targets=[locust_service]
            )
    