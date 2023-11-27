# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""  This Lambda function
"""
import json
import logging
import os
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

region = os.environ["REGION"]
account_id = os.environ["ACCOUNT_ID"]
snstopic = os.environ["SNS_TOPIC_ARN"]
soft_fail = os.environ["SOFT_FAIL"]
hard_fail = os.environ["HARD_FAIL"]

client_accessanalyzer = boto3.client("accessanalyzer")
client_sns = boto3.client("sns")


def lambda_handler(event, context):
    """Lambda Handler"""
    logger.info(f"### RAW Event {json.dumps(event)}")
    parsed_event = json.loads(event["Records"][0]["Sns"]["Message"])
    logger.info(f"### Parsed Event {parsed_event}")
    result_validate = client_accessanalyzer.validate_policy(
        policyDocument=json.dumps(parsed_event["policy_document"]),
        policyType="IDENTITY_POLICY",
        locale="EN",
    )
    logger.info(f"### Access Analyzer Result {result_validate}")
    policy_reference = parsed_event["policy_reference"]
    policy_document = parsed_event["policy_document"]
    trigger = parsed_event["trigger"]
    useridentity_arn = parsed_event["agent_role_arn"]
    event_time = parsed_event["event_time"]
    target = parsed_event["target_principal"]
    findings = result_validate["findings"]
    if findings:
        message = (
            f"Critical permissions evaluation for IAM Policy {policy_reference} \n\n"
            f"Action triggering policy evaluation: {trigger} \n\n"
            f"Role performing action: {useridentity_arn} \n\n"
            f"Event time: {event_time} \n\n"
            f"Target principal: {target} \n\n"
            f"Policy Document: {json.dumps(policy_document, indent=4)} \n\n"
            f"Evaluation: {findings}"
        )
        subject = "Policy Document Check for Policy Validation"
        response = client_sns.publish(
            TopicArn=snstopic,
            Message=message,
            Subject=subject,
        )
        logger.info(f"Notification sent: {response}")
        logger.info(f"notification message: {message}")
