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

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.get_cdk_context()


        #Build new VPC
        self.vpc = ec2.Vpc(
            self, "loadgenvpc",
            cidr=self.vpc_cidr,
            subnet_configuration=[
                {"cidrMask": 24, "name": "ecsvpc", "subnetType": ec2.SubnetType.PUBLIC},
                {"cidrMask": 24, "name": "ecsprivatevpc", "subnetType": ec2.SubnetType.PRIVATE}
            ]
        )


        #ECS cluster for the loadgen
        self.loadgen_cluster = ecs.Cluster(
            self, "Loadgen-Cluster",
            vpc=self.vpc
        )

        #Just using base ENI count, not caring about having ENI trunking turned on
        client = boto3.client('ec2')
        response = client.describe_instance_types(InstanceTypes=[self.ecs_instance_type])
        eni_per_instance = response['InstanceTypes'][0]['NetworkInfo']['MaximumNetworkInterfaces']


        number_of_instances = math.ceil((self.number_of_workers + 1) / (eni_per_instance-1))
        self.loadgen_cluster.add_capacity("AsgSpot",
                                          max_capacity=number_of_instances * 2,
                                          min_capacity=number_of_instances,
                                          instance_type=ec2.InstanceType(self.ecs_instance_type),
                                          spot_price="0.07",
                                          spot_instance_draining=True
                                         )
        #cloudmap for service discovery so slaves can lookup mast via dns
        self.loadgen_cluster.add_default_cloud_map_namespace(name = self.cloudmap_namespace)

        #Create a graph widget to track reservation metrics for our cluster
        ecs_widget = cw.GraphWidget(
            left=[self.loadgen_cluster.metric_cpu_reservation()],
            right=[self.loadgen_cluster.metric_memory_reservation()],
            title="ECS - CPU and Memory Reservation",
            )

        #CloudWatch dashboard to monitor our stuff
        self.dashboard = cw.Dashboard(self, "Locustdashboard")
        self.dashboard.add_widgets(ecs_widget)

        if not self.distributed_locust:
            role = "standalone"
            locustContainer(self, "locust" + role, self.vpc, self.loadgen_cluster, role, self.target_url)
        else:
            role = "master"
            master_construct = locustContainer(self, "locust" + role, self.vpc,
                                               self.loadgen_cluster, role, self.target_url)

            lb_widget = cw.GraphWidget(
                left=[master_construct.lb.metric_active_connection_count(),
                      master_construct.lb.metric_target_response_time()],
                right=[master_construct.lb.metric_request_count()],
                title="Load Balancer")

            self.dashboard.add_widgets(lb_widget)

            role = "slave"
            worker_construct = locustContainer(self, "locust" + role, self.vpc,
                                               self.loadgen_cluster, role, self.target_url,
                                               self.number_of_workers)
            worker_construct.node.add_dependency(master_construct)

    def get_cdk_context(self):
    # grab stuff from context

        self.number_of_workers = int(self.node.try_get_context("number_of_workers"))
        self.ecs_instance_type = self.node.try_get_context("ecs_instance_type")
        self.vpc_cidr = self.node.try_get_context("vpc_cidr")
        self.distributed_locust = self.node.try_get_context("distributed_locust")
        self.cloudmap_namespace = self.node.try_get_context("cloudmap_namespace")
        self.target_url = self.node.try_get_context("target_url")
