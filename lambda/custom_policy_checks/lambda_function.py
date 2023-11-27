# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""  This Lambda function
"""
import json
import logging
import boto3
import os

snstopic = os.environ["SNS_TOPIC_ARN"]
s3bucket = os.environ["BUCKET"]
s3key = os.environ["KEY"]

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client_s3 = boto3.client("s3")
client_sns = boto3.client("sns")
client_accessanalyzer = boto3.client("accessanalyzer")


def lambda_handler(event, context):
    """Lambda Handler"""
    logger.info(f"### RAW Event {json.dumps(event)}")
    logger.info(f"Bucket {s3bucket} Key {s3key}")
    s3object = client_s3.get_object(Bucket=s3bucket, Key=s3key)
    privileged_actions = s3object["Body"].read().decode("UTF-8").splitlines()
    logger.info(f"### Privileged actions {privileged_actions}")
    parsed_event = json.loads(event["Records"][0]["Sns"]["Message"])
    logger.info(f"### Parsed Event {parsed_event}")
    policy_document = json.dumps(parsed_event["policy_document"])
    results = []
    for action in privileged_actions:
        response = client_accessanalyzer.check_access_not_granted(
            policyDocument=policy_document,
            policyType="IDENTITY_POLICY",
            access=[{"actions": [action]}],
        )
        if response["result"] == "FAIL":
            results.append([action, response["reasons"]])
    logger.info(f"### Results {results}")
    if results:
        policy_reference = parsed_event["policy_reference"]
        policy_document = parsed_event["policy_document"]
        trigger = parsed_event["trigger"]
        useridentity_arn = parsed_event["agent_role_arn"]
        event_time = parsed_event["event_time"]
        target = parsed_event["target_principal"]
        message = (
            f"Custom policy checks for IAM Policy {policy_reference} \n\n"
            f"Action triggering policy evaluation: {trigger} \n\n"
            f"Role performing action: {useridentity_arn} \n\n"
            f"Event time: {event_time} \n\n"
            f"Target principal: {target} \n\n"
            f"Policy Document: {json.dumps(policy_document, indent=4)} \n\n"
            f"Evaluation: {results}"
        )
        subject = "Policy Document Check for Custom Policy Checks"
        response = client_sns.publish(
            TopicArn=snstopic,
            Message=message,
            Subject=subject,
        )
        logger.info(f"Notification sent: {response}")
        logger.info(f"notification message: {message}")