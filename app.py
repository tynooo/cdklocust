#!/usr/bin/env python3

from aws_cdk import core

from cdklocust.cdklocust_stack import CdklocustStack


'''
If you need to change things like vpc cidr, number of slave containers, 
or instance type do that in the class def
'''

app = core.App()
CdklocustStack(app, "cdklocust", 
    env={'region': 'ap-southeast-2'},
    distributed_locust = True,
    target_url="http://localhost/"
)
app.synth()
