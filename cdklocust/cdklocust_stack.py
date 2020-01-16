from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam
    )
from cdklocust.locust_container import locustContainer

class CdklocustStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, distributed_locust: bool, target_url: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        vpc_cidr = "10.51.0.0/16"
        number_of_slaves = 3
        ecs_instance_type="c5.large"
        #Build new VPC
        vpc = ec2.Vpc(
            self, "loadgenvpc",
            cidr=vpc_cidr,
            subnet_configuration=[
                { "cidrMask": 24, "name": "ecsvpc", "subnetType": ec2.SubnetType.PUBLIC},
                { "cidrMask": 24, "name": "ecsprivatevpc", "subnetType": ec2.SubnetType.PRIVATE, }
            ]
        )
         
         
        #ECS cluster for the loadgen
        loadgen_cluster = ecs.Cluster(
            self, "Loadgen-Cluster",
            vpc=vpc
        )
        
        loadgen_cluster.add_capacity("AsgSpot",
            max_capacity=2,
            min_capacity=2,
            desired_capacity=2,
            instance_type=ec2.InstanceType(ecs_instance_type),
            spot_price="0.07",
            # Enable the Automated Spot Draining support for Amazon ECS
            spot_instance_draining=True
        )
        #cloudmap for service discovery so slaves can lookup mast via dns
        loadgen_cluster.add_default_cloud_map_namespace(name="loadgen")
        
        if not distributed_locust:
            role = "standalone"
            locustContainer(self, "locust" + role, vpc, loadgen_cluster, role, target_url)
        else:
            role = "master"
            locustContainer(self, "locust" + role, vpc, loadgen_cluster, role, target_url)
            role = "slave"
            locustContainer(self, "locust" + role, vpc, loadgen_cluster, role, target_url, number_of_slaves)