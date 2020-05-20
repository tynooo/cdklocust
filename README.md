
# Containerised Locust load generation in CDK

This is an example of how to build a distributed Locust swarm in ECS (on ec2 Spot) using CDK in python.


## Structure

app.py is the entry point. In here you can set the Deployment region and account


Most of the parameters are set via the app context in cdk.json:
 - VPC config
 - ECS cluster instance type
 - Number of locust workers 
 - CloudMap namespace (I've used loadgen, but you could use an existing namespace and/or route53 domain)
 - Whether Locust is distributed or standalone
 - The target url

cdklocust/cdklocustinfra_stack.py defines the VPC, and can be used to define other resources that exist outside the Locust services. 

cdklocust/cdklocust_stack.py defines the ECS cluster and invokes the locust_container construct to build the services themselves..

cdklocust/locust_container (yes, I could have named that better) is a CDK construct class that defines the task and service properties to run Locust in ECS 

locust/Dockerfile is the dockerfile that is used to generate the Locust image. This one just grabs the Locust.io image and adds locustfile.py to it.

locust/locustfile.py defines the locust configuration. Check out the docs for more info https://docs.locust.io/en/stable/writing-a-locustfile.html

## Getting it running

Assuming you have Python3 and CDK installed

Clone this repo and get your environment ready

```
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
npm -g upgrade
```



Then run ```cdk deploy cdklocust``` to deploy to your account, if the cdklocustinfra stack isn't up already, it'll create that too. 

When you're done run ```cdk destroy cdkinfra``` to tear it all down, or ```cdk destroy cdklocust``` to only destroy the ECS cluster, services, and ALB.