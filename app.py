#!/usr/bin/env python3

from aws_cdk import core

from cdklocust.cdklocust_stack import CdklocustStack


app = core.App()
CdklocustStack(app, "cdklocust")

app.synth()
