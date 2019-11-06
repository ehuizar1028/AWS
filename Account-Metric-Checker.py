import boto3
import time
import sys

profile=sys.argv[1]

region_session = boto3.Session(region_name='us-east-1', profile_name=profile)
r = region_session.client('ec2')
regions = [region['RegionName'] for region in r.describe_regions()['Regions']]


def checkVolumes(region):
    volume_session = boto3.Session(region_name=region, profile_name=profile)
    ec = volume_session.client('ec2')
    vol = ec.describe_volumes(Filters=[{'Name': 'status', 'Values': ['available']}])["Volumes"]
    return len(vol)

def checkSnapshots(region):
    snapshot_session = boto3.Session(region_name=region, profile_name=profile)
    ec = snapshot_session.client('ec2')
    snapshots = ec.describe_snapshots(OwnerIds=['self'])["Snapshots"]
    return len(snapshots)

def checkAttachedVolume(region):
    attached_session = boto3.Session(region_name=region, profile_name=profile)
    ec = attached_session.client('ec2')
    allInstances = ec.describe_instances()['Reservations']
    allInstances_AttachedVolumes=[]
    for i in allInstances:
        c = len(i["Instances"][0]['BlockDeviceMappings'])
        if c > 2:
            allInstances_AttachedVolumes.append(c)
    return len(allInstances_AttachedVolumes)

def checkStoppedInstances(region):
    stopped_session = boto3.Session(region_name=region, profile_name=profile)
    ec = stopped_session.client('ec2')
    allStoppedInstances = ec.describe_instances(Filters=[{'Name':'instance-state-name', 'Values':['stopped']}])['Reservations']
    return len(allStoppedInstances)

def checkEIPs(region):
    eip_session = boto3.Session(region_name=region, profile_name=profile)
    ec = eip_session.client('ec2')
    allEIPs = ec.describe_addresses(Filters=[{'Name':'instance-id', "Values":[""]}])["Addresses"]
    return len(allEIPs)

def main():
    metric=sys.argv[2]
    #metric="unattached-eips"
    if metric == "snapshots":
        snapshot_length = []
        for reg in regions:
            snapshotCount=checkSnapshots(reg)
            snapshot_length.append(snapshotCount)
        print "AWSAccountMetrics.{}.snapshotCount {} {}".format(profile, sum(snapshot_length), time.time())
    elif metric == "volumes":
        volume_length = []
        for reg in regions:
            volumeCount=checkVolumes(reg)
            volume_length.append(volumeCount)
        print "AWSAccountMetrics.{}.volumeCount {} {}".format(profile, sum(volume_length), time.time())
    elif metric == "attached-volumes":
        attachedVolumes_length = []
        for reg in regions:
            attachedCount=checkAttachedVolume(reg)
            attachedVolumes_length.append(attachedCount)
        print "AWSAccountMetrics.{}.attachedVolumesGreaterThanTwo {} {}".format(profile, sum(attachedVolumes_length), time.time())
    elif metric == "stopped-instances":
        stopped_instances_count = []
        for reg in regions:
            c = checkStoppedInstances(reg)
            stopped_instances_count.append(c)
        print "AWSAccountMetrics.{}.stoppedInstances {} {}".format(profile, sum(stopped_instances_count), time.time())
    elif metric == "unattached-eips":
        eip_count=[]
        for reg in regions:
            c = checkEIPs(reg)
            eip_count.append(c)
        print "AWSAccountMetrics.{}.unattachedEIPCount {} {}".format(profile, sum(eip_count), time.time())


main()
