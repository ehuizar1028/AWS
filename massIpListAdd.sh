#!/bin/bash

#This script allows to add IP addresses to an AWS Security Group stored in an excel file. Really useful for adding a handful of
#IPs 

while getopts "f:t:i:c:g:r:h" OPTION
do
	case $OPTION in
		f)
			from=$OPTARG
			;;
		t)
			to=$OPTARG
			;;
    i)
			ips=$(cat $OPTARG)
			;;
    d)
      desc=$OPTARG
      ;;
		c)
      AWS_PROFILE=$OPTARG
      ;;
		g)
			groupID=$OPTARG
			;;
		r)
		  region=$OPTARG
			;;
		\?|h )
			echo "USAGE:"
			echo "-f = FROM port                 -- REQUIRED"
			echo "-t = TO port                   -- OPTIONAL: if not included, then TO = FROM"
			echo "-i = Path to ip list           -- REQUIRED"
			#echo "-d = Description               -- OPTIONAL"
			echo "-c = AWS PROFILE (4 Letter ID) -- REQUIRED"
			echo "-g = Security Group ID         -- REQUIRED"
			echo "-r = REGION                    -- OPTIONAL: If not included, then region = us-east-1"
			exit 1
			;;
	esac
done
if ((OPTIND == 1))
then
    echo "No options specified... Type -h for help"
		exit 1
fi
if [ -z $to ]; then
	to=$from
fi
if [ -z $region ]; then
	$region="us-east-1"
fi
echo "Enter Meaningful Comments: "
read comments
if [[ "$comments" == "" ]]; then
  echo "Comments are required. If there is no associated ticket"
  exit 1
fi
desc="$comments - Added By $USER ON $(date +%F)"
echo "DESCRIPTION: "
echo "$desc"
if [ -z "$from" ] || [ -z "$ips" ] || [ -z "$AWS_PROFILE" ] || [ -z "$groupID" ]; then
	echo "Not Enough Options. Type -h for help"
	exit 1
fi
for i in $ips;
   do
   echo "Adding Ingress Rule for IP: $i"
   aws \
   --profile $AWS_PROFILE \
   --region $region\
   ec2 authorize-security-group-ingress \
   --group-id $groupID \
   --ip-permissions IpProtocol=tcp,FromPort=$from,ToPort=$to,IpRanges="[{CidrIp=\"$i\",Description=\"$desc\"}]";
done
