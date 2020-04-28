import math
import boto3
from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_cloudwatch as cw
    )

from cdklocust.locust_container import locustContainer

class CdklocustStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, distributed_locust: bool, target_url: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        vpc_cidr = "10.51.0.0/16"
        number_of_slaves = 3
        ecs_instance_type = "c5.large"
        #Build new VPC
        vpc = ec2.Vpc(
            self, "loadgenvpc",
            cidr=vpc_cidr,
            subnet_configuration=[
                {"cidrMask": 24, "name": "ecsvpc", "subnetType": ec2.SubnetType.PUBLIC},
                {"cidrMask": 24, "name": "ecsprivatevpc", "subnetType": ec2.SubnetType.PRIVATE}
            ]
        )


        #ECS cluster for the loadgen
        loadgen_cluster = ecs.Cluster(
            self, "Loadgen-Cluster",
            vpc=vpc
        )

        client = boto3.client('ec2')
        response = client.describe_instance_types(InstanceTypes=[ecs_instance_type])
        eni_per_instance = response['InstanceTypes'][0]['NetworkInfo']['MaximumNetworkInterfaces']


        number_of_instances = math.ceil((number_of_slaves + 1) / (eni_per_instance-1))
        loadgen_cluster.add_capacity("AsgSpot",
                                     max_capacity=number_of_instances * 2,
                                     min_capacity=number_of_instances,
                                     instance_type=ec2.InstanceType(ecs_instance_type),
                                     spot_price="0.07",
                                     # Enable the Automated Spot Draining support for Amazon ECS
                                     spot_instance_draining=True
                                    )
        #cloudmap for service discovery so slaves can lookup mast via dns
        loadgen_cluster.add_default_cloud_map_namespace(name="loadgen")

        #Create a graph widget to track reservation metrics for our cluster
        ecs_widget = cw.GraphWidget(
            left=[loadgen_cluster.metric_cpu_reservation()],
            right=[loadgen_cluster.metric_memory_reservation()],
            title="ECS - CPU and Memory Reservation",
            )

        #CloudWatch dashboard to monitor our stuff
        dashboard = cw.Dashboard(self, "Locustdashboard")
        dashboard.add_widgets(ecs_widget)

        if not distributed_locust:
            role = "standalone"
            locustContainer(self, "locust" + role, vpc, loadgen_cluster, role, target_url)
        else:
            role = "master"
            master_construct = locustContainer(self, "locust" + role, vpc,
                                              loadgen_cluster, role, target_url)

            lb_widget = cw.GraphWidget(
                left=[master_construct.lb.metric_active_connection_count(),
                      master_construct.lb.metric_target_response_time()],
                right=[master_construct.lb.metric_request_count()],
                title="Load Balancer")

            dashboard.add_widgets(lb_widget)

            role = "slave"
            slave_construct = locustContainer(self, "locust" + role, vpc,
                                              loadgen_cluster, role, target_url,
                                              number_of_slaves)
            slave_construct.node.add_dependency(master_construct)
