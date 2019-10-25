import boto3

##Ability to restore from snapshots alot faster. This script DOESNT restore multiple instances, 
##but this script can be ran in parallel with other instances of this script in order to restore 
##multiple instances

def getSnapshotsList(client, instance):
    snapshotInfo = []
    print("Retrieving Snapshots")
    snapshots = client.describe_snapshots(Filters = [{"Name" : "status", "Values" : ["completed"]}], OwnerIds=['self'])["Snapshots"]
    for s in snapshots:
        description = s["Description"]
        createTime = s["StartTime"]
        snapshotID = s["SnapshotId"]
        volumeSize = s["VolumeSize"]
        try:
            tags = s["Tags"]
            for t in tags:
                if t["Key"] == "Name":
                    tagInfo = t["Value"]
        except:
            pass
        if instance in description or instance in tagInfo:
            snapshotInfo.append({"CreateTime" : createTime,  "SnapshotID" : snapshotID,  "VolumeSize" : volumeSize})
            print("Creation Time: {} | SnapshotID: {} | VolumeSize: {}" .format(createTime, snapshotID, volumeSize))
    return snapshotInfo


def getInstances(client):
    instanceInfo = []
    instances = client.describe_instances()
    for i in instances["Reservations"]:
        instanceID = i["Instances"][0]["InstanceId"]
        az = i["Instances"][0]["Placement"]["AvailabilityZone"]
        tags = i["Instances"][0]["Tags"]
        for t in tags:
            if t["Key"] == "Name":
                instanceName = t["Value"]
        instanceInfo.append({"InstanceID" : instanceID, "InstanceName" : instanceName , "AZ" : az})
    return instanceInfo

def createVolume(client, az, SnapshotId):
    vol_status = client.create_volume(
        AvailabilityZone=az,
        SnapshotId=SnapshotId,
        VolumeType="gp2"
    )
    return vol_status["VolumeId"]

def shutdownServer(client, instanceID):
    print("STOPPING INSTANCE {}...".format(instanceID))
    client.stop_instances(
        InstanceIds=[instanceID]
    )
    w = client.get_waiter('instance_stopped')
    w.wait(InstanceIds=[instanceID])
    print("INSTANCE {} IS STOPPED".format(instanceID))


def volumeActions(client, instanceID, volumeFromSnapshot_ID):
    instance = client.describe_instances(InstanceIds=[instanceID])
    mounts = instance["Reservations"][0]["Instances"][0]["BlockDeviceMappings"]
    aval_volumes = []
    print("This instance has the following mounts")
    for b in mounts:
        volumeID = b["Ebs"]["VolumeId"]
        vol_describe = client.describe_volumes(VolumeIds=[volumeID])
        try:
            tags = vol_describe["Volumes"][0]["Tags"]
            for t in tags:
                if t["Key"] == "Name":
                    desc = t["Value"]
        except KeyError:
            desc = "No Tags Defined"

        print("VolumeID: {} | Mount: {} | NAME-Tag: {}".format(volumeID, b["DeviceName"], desc))
        aval_volumes.append(volumeID)
    vol_mount_id = input("Choose the volumeID to unmount: ")
    while vol_mount_id not in aval_volumes:
        vol_mount_id = input("Your selection is invalid, select a VolumeID listed above:")

    vol_mount = input("Enter New Mount Point to use: ")
    detach_response = client.detach_volume(
        InstanceId=instanceID,
        VolumeId=volumeID
    )
    if detach_response["ResponseMetadata"]["HTTPStatusCode"] != 200:
        print("There was an issue deattaching the volume... HTTP ERROR: ")
        print(detach_response["ResponseMetadata"]["HTTPStatusCode"])
        exit(1)

    print("Deattching Old Volume...")
    w = client.get_waiter('volume_available')
    w.wait(VolumeIds=[vol_mount_id])
    attachResponse = client.attach_volume(
        InstanceId=instanceID,
        VolumeId=volumeFromSnapshot_ID,
        Device=vol_mount
    )
    print("Attaching New Volume...")
    if attachResponse["ResponseMetadata"]["HTTPStatusCode"] != 200:
        print("There was an issue attaching the volume... HTTP ERROR: ")
        print(detach_response["ResponseMetadata"]["HTTPStatusCode"])
        exit(1)
    print("BOOTING UP INSTANCE...")
    client.start_instances(
        InstanceIds=[instanceID]
    )

def main():
    ctmsp_client = input("Select a PROFILE in the AWS Config: ")
    region = ""
    if region == "":
        region = "us-east-1"
    session = boto3.Session(profile_name=ctmsp_client, region_name=region)
    client = session.client('ec2')
    listOfInstnaces = getInstances(client)
    for l in listOfInstnaces:
        print("InstanceID: {} | InstanceName : {} | AZ : {}".format(l["InstanceID"], l["InstanceName"], l["AZ"]))
    instance = input("Please Select an InstanceID: ")
    AZ = input("Select the AZ you want the volume to be in: ")
    getSnapshotsList(client, instance)
    snapshot = input("Select A Snapshot: ")
    volID = createVolume(client, AZ, snapshot)
    shutdownServer(client, instance)
    volumeActions(client, instance, volID)


main()
