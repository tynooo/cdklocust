
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

locust/Dockerfile is the dockerfile that is used to generate the Locust image. This one just grabs the latest Locust.io image and adds locustfile.py to it.

locust/locustfile.py defines the locust configuration. Check out the docs for more info https://docs.locust.io/en/stable/writing-a-locustfile.html

## Getting it running

Assuming you have Python3 and CDK installed

Clone this repo and get your environment ready

```
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
```

Then run ```cdk deploy``` to deploy to your account. 

When you're done run ```cdk destroy``` to tear it down.