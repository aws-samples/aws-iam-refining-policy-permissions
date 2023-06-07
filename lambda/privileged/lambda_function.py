# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""  This Lambda function is triggered by EventBridge Rules based on the following
    API calls: "AttachGroupPolicy", "AttachRolePolicy", "AttachUserPolicy",
    "CreatePolicy", "CreatePolicyVersion", "PutGroupPolicy", "PutRolePolicy",
    "PutUserPolicy", "SetDefaultPolicyVersion". The function inspects the policy
    document looking for privileged actions listed in the file privileged.txt.
    Sends an alert via SNS whenever there is a match.
"""
import json
import logging
import boto3
import os
import fnmatch

sns_topic_arn = os.environ["SNS_TOPIC_ARN"]
s3bucket = os.environ["BUCKET"]
s3key = os.environ["KEY"]

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client_iam = boto3.client("iam")
client_s3 = boto3.client("s3")
client_sns = boto3.client("sns")


def lambda_handler(event, context):
    """Lambda Handler"""
    # These actions track creation, update, assignment, and changes in default of identity-based policies
    # https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html#policies_id-based
    # https://docs.aws.amazon.com/IAM/latest/APIReference/API_Operations.html
    actions = [
        "AttachGroupPolicy",
        "AttachRolePolicy",
        "AttachUserPolicy",
        "CreatePolicy",
        "CreatePolicyVersion",
        "PutGroupPolicy",
        "PutRolePolicy",
        "PutUserPolicy",
        "SetDefaultPolicyVersion",
    ]
    requestparameters = event["detail"]["requestParameters"]
    responseelements = event["detail"]["responseElements"]
    logger.info(f"### RAW Event {json.dumps(event)}")
    action = event["detail"]["eventName"]
    logger.info(f"### Event requestParameters {requestparameters}")
    logger.info(f"### Event responseElements {responseelements}")
    # Read list of privileged action to be monitored in IAM Policies from
    # file `privileged.txt` stored in an S3 Bucket
    logger.info(f"Bucket {s3bucket} Key {s3key}")
    s3object = client_s3.get_object(Bucket=s3bucket, Key=s3key)
    privileged_actions = s3object["Body"].read().decode("UTF-8").splitlines()
    logger.info(f"### Privileged actions {privileged_actions}")
    if action in actions:
        logger.info(f"### API call supported {action}")
        # These actions monitor the assignment of identity-based policies to IAM Principals
        if action in [
            "AttachGroupPolicy",
            "AttachRolePolicy",
            "AttachUserPolicy",
            "SetDefaultPolicyVersion"
        ]:
            logger.info(f"### processing {action}")
            policy_arn = requestparameters["policyArn"]
            get_policy = client_iam.get_policy(
                PolicyArn=policy_arn
            )
            # retrieves policy document for processing
            get_policy_version = client_iam.get_policy_version(
                PolicyArn=policy_arn,
                VersionId=get_policy["Policy"]["DefaultVersionId"]
            )
            policy_document = get_policy_version["PolicyVersion"]["Document"]
            policy_reference = event["detail"]["requestParameters"]["policyArn"]
        # These actions monitor creation and changes to principal IAM Policies
        # They embed the policy document in `requestParameters`
        elif action in [
            "CreatePolicy",
            "PutRolePolicy",
            "PutGroupPolicy",
            "PutUserPolicy",
        ]:
            logger.info(f'### processing {action}')
            policy_document = json.loads(requestparameters["policyDocument"])
            policy_reference = event["detail"]["requestParameters"]["policyName"]
        # This action monitors changes in default IAM Policy version
        elif action in [
            "CreatePolicyVersion",
        ]:
            logger.info(f'### processing {action}')
            policy_document = json.loads(requestparameters["policyDocument"])
            policy_reference = event["detail"]["requestParameters"]["policyArn"]
        target = "None"
        if "roleName" in event["detail"]["requestParameters"]:
            target = event["detail"]["requestParameters"]["roleName"]
        if "groupName" in event["detail"]["requestParameters"]:
            target = event["detail"]["requestParameters"]["groupName"]
        if "userName" in event["detail"]["requestParameters"]:
            target = event["detail"]["requestParameters"]["userName"]
        if target != "None":
            logger.info(f"found target {target}")
        logger.info(f"found policy {policy_reference}")
        logger.info(f"found policy document {policy_document}")
        actions_matched = []
        send_sns = False
        for statement in policy_document["Statement"]:
            if type(statement["Action"]) == list:
                for action_ in statement["Action"]:
                    logger.info(f"action to be evaluated: {action_}")
                    if len(fnmatch.filter(privileged_actions, action_)) > 0:
                        actions_matched.append(action_)
                        send_sns = True
            else:
                action_ = statement["Action"]
                logger.info(f"action to be evaluated: {action_}")
                if len(fnmatch.filter(privileged_actions, statement["Action"])) > 0:
                    actions_matched.append(action_)
                    send_sns = True
        if send_sns:
            trigger = event["detail"]["eventName"],
            useridentity_arn = event["detail"]["userIdentity"]["arn"],
            event_time = event["detail"]["eventTime"],
            message = (
                f"Privileged action(s) have been detected in identity-based policy {policy_reference} \n\n"
                f"Action triggering policy linting: {trigger} \n\n"
                f"Role performing action: {useridentity_arn} \n\n"
                f"Event time: {event_time} \n\n"
                f"Target principal: {target} \n\n"
                f"Policy Document: {json.dumps(policy_document, indent=4)}"
                f"Privileged actions found: {actions_matched}"
            )
            subject = "Policy Document contains privileged action(s)"
            response = client_sns.publish(
                TopicArn=sns_topic_arn,
                Message=message,
                Subject=subject,
            )
            logger.info(f"Notification sent: {response}")
            logger.info(f"notification message: {message}")
    else:
        logger.info("### API call not supported")
        logger.info(action)
