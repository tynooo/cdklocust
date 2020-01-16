
# Containerised Locust load generation in CDK

This is an example of how to build a distributed Locust swarm in ECS (on ec2 Spot) using CDK in python.


## Structure

app.py is the entry point. In here you can set:
 - Deployment region
 - Whether Locust is distributed or standalone
 - The target url

cdklocust/cdklocust_stack.py defines the VPC and ECS cluster. In here you can adjust:
 - VPC config
 - ECS cluster specs (cluster size, instance type, spot bid)
 - Number of locust slaves 
 - CloudMap namespace (I've used loadgen, but you could use an existing namespace and/or route53 domain)

cdklocust/locust_container (yes, I could have named that better) is a CDK construct class that defines the task and service properties to run Locust in ECS 

## Useful commands summarised from the CDK app build
There's a virtualenv created, so activate it using 

```
$ source .env/bin/activate
```
Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

