#!/bin/bash

##Deploys to Lambda.

AWS_profiles=(profile1 profile2 profile3 etc)
region="us-east-1"
RETENTION="14"
role_name="roleName"
policy_name="policyName"
description="Policy for lambda functions"
function_name="lambda-function-${region}"
function_description="descriptionForLambda"
handler="Lambda.main"
timeout="300"
memory_size="128"
put_rule="every_2_minute-${region}"
rate="rate(2 minutes)"
rate_description="every 2 minutes"
runtime="python3.7"
statement_id="lambda-${region}"
principal="events.amazonaws.com"
action="lambda:invokefunction"


for ((i = 0; i < ${#AWS_profiles[@]}; i++))
  do
    zip -j lambda.zip file1.zip file2.zip

    aws logs create-log-group --log-group-name /aws/lambda/${function_name} --profile ${AWS_profiles[$i]} --region ${region}
    aws logs put-retention-policy --log-group-name /aws/lambda/${function_name} --retention-in-days ${RETENTION} --profile ${AWS_profiles[$i]} --region ${region}

    ACCOUNT=`aws sts get-caller-identity --profile ${AWS_profiles[$i]} --region ${region} --query 'Account' --output text`
    echo "creating role..."

    aws iam create-role --role-name ${role_name} --assume-role-policy-document file://role_trust.json --description "${description}" --profile ${AWS_profiles[$i]} --region ${region}
    sleep 2
    echo "putting policy..."
    aws iam put-role-policy --role-name ${role_name} --policy-name ${policy_name} --policy-document file://role_perms.json --profile ${AWS_profiles[$i]} --region ${region}
    sleep 5
    echo "getting rule arn..."
    role_arn=`aws iam get-role --role-name lambda_role --query "Role.Arn" --profile ${AWS_profiles[$i]} --region ${region} --output text`

    echo "creating function..."
    aws lambda create-function --function-name ${function_name} --runtime ${runtime} --role ${role_arn} --handler ${handler} --description "${function_description}" --zip-file 'fileb://lambda.zip' --environment Variables="{client=${AWS_profiles[$i]},sensu_pass=M511gr32h576L6T,sensu_user=sensu-api}" --timeout ${timeout} --memory-size ${memory_size} --publish --profile ${AWS_profiles[$i]} --region ${region}

    echo "putting events rule..."
    aws events put-rule --name ${put_rule} --schedule-expression "${rate}" --state ENABLED --role-arn ${role_arn} --description "${rate_description}" --profile ${AWS_profiles[$i]} --region ${region} --output text
    sleep 5

    echo "getting create source arn..."
    #create_source_arn=`aws events describe-rule --name ${create_put_rule} --profile ${AWS_profiles[$i]} --region ${region} --output text`
    create_source_arn="arn:aws:events:"${region}":"${ACCOUNT}":rule/${put_rule}"
    sleep 5
    echo "adding permission..."
    aws lambda add-permission --function-name ${function_name} --statement-id "${statement_id}" --action "${action}" --principal ${principal} --source-arn "${create_source_arn}" --profile ${AWS_profiles[$i]} --region ${region} --output text
    sleep 5

    echo "putting events target..."
    #echo "arn:aws:lambda:${region}:${ACCOUNT}:function:${function_name}"
    aws events put-targets --rule "${put_rule}" --targets "Id"="1","Arn"="arn:aws:lambda:${region}:${ACCOUNT}:function:${function_name}"  --profile "${AWS_profiles[$i]}" --region "${region}"
    sleep 5

    ###



done
