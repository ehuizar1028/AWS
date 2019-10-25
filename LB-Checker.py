import boto3
import sys, json, os

def getLB(lbName, lbType):
    if lbType == "elb":
        elb = boto3.client("elb")
        elbDescriptions = elb.describe_load_balancers(LoadBalancerNames=[lbName])
        elbStates = elb.describe_instance_health(LoadBalancerName=lbName)["InstanceStates"]
        numOfNodes = len(elbDescriptions["LoadBalancerDescriptions"][0]["Instances"])
        instanceStats = {
            "OutOfServiceInstances": [],
            "LBCount": numOfNodes
        }
        for h in elbStates:
            if h['State'] == 'OutOfService':
                instanceStats["OutOfServiceInstances"].append(h["InstanceId"])
        return instanceStats
    else:
        alb = boto3.client("elbv2")
        tgARN = alb.describe_target_groups(Names=[lbName])['TargetGroups'][0]["TargetGroupArn"]
        tg = alb.describe_target_health(TargetGroupArn=tgARN)["TargetHealthDescriptions"]
        tgCount = len(tg)
        instanceStats = {
            "OutOfServiceInstances": [],
            "LBCount": tgCount
        }
        for t in tg:
            state = t['TargetHealth']['State']
            instance = t['Target']['Id']
            if state == "unhealthy":
                instanceStats.append(instance)
        return instanceStats
