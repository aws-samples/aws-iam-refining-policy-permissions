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

sns_topic_arn = os.environ["SNS_TOPIC_ARN"]

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client_iam = boto3.client("iam")
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
    policy_reference = None
    policy_document = None
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
        target = None
        if "roleName" in event["detail"]["requestParameters"]:
            target = event["detail"]["requestParameters"]["roleName"]
        if "groupName" in event["detail"]["requestParameters"]:
            target = event["detail"]["requestParameters"]["groupName"]
        if "userName" in event["detail"]["requestParameters"]:
            target = event["detail"]["requestParameters"]["userName"]
        if target:
            logger.info(f"found target {target}")
        logger.info(f"found policy {policy_reference}")
        logger.info(f"found policy document {policy_document}")
        message = {
            "policy_reference":  policy_reference,
            "trigger": event["detail"]["eventName"],
            "agent_role_arn": event["detail"]["userIdentity"]["arn"],
            "event_time": event["detail"]["eventTime"],
            "target_principal": target,
            "policy_document": policy_document,
        }
        response = client_sns.publish(
            TopicArn=sns_topic_arn,
            Message=json.dumps(message),
        )
        logger.info(f"Notification sent: {response}")
        logger.info(f"notification message: {message}")