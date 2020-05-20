#!/usr/bin/env python3
import os
from aws_cdk import core

from cdklocust.cdklocust_stack import CdklocustStack


'''
If you need to change things like vpc cidr, number of slave containers,
or instance type do that in the class def
'''

app = core.App()

ACCOUNT = app.node.try_get_context('account') or os.environ.get(
    'CDK_DEFAULT_ACCOUNT', 'unknown')
REGION = app.node.try_get_context('region') or os.environ.get(
    'CDK_DEFAULT_REGION', 'unknown')

AWS_ENV = core.Environment(region=REGION, account=ACCOUNT)

CdklocustStack(app, "cdklocust", env=AWS_ENV)

app.synth()
