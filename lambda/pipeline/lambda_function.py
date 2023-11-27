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

snstopic = os.environ["SNS_TOPIC_ARN"]

client_sns = boto3.client("sns")


def lambda_handler(event, context):
    """Lambda Handler"""
    logger.info(f"### RAW Event {json.dumps(event)}")
    parsed_event = json.loads(event["Records"][0]["Sns"]["Message"])
    logger.info(f"### Parsed Event {parsed_event}")
    build_status = parsed_event["detail"]["build-status"]
    build_id = parsed_event["detail"]["build-id"]
    project_name = parsed_event["detail"]["project-name"]
    initiator = parsed_event["detail"]["additional-information"]["initiator"]
    build_start_time = parsed_event["detail"]["additional-information"]["build-start-time"]
    logs = parsed_event["detail"]["additional-information"]["logs"]["deep-link"]
    context = []
    for phase in parsed_event["detail"]["additional-information"]["phases"]:
        if "phase-status" in phase:
            if phase["phase-status"] == "FAILED":
                context.append(phase["phase-context"])
    message = (
        f"Pipeline Build Result for build-id: {build_id}\n\n"
        f"Status: {build_status} \n\n"
        f"Project Name: {project_name} \n\n"
        f"Initiator: {initiator} \n\n"
        f"Build start time: {build_start_time} \n\n"
        f"URL for logs: {logs} \n\n"
        f"Context: {context}"
    )
    subject = "Pipeline Build Result"
    response = client_sns.publish(
        TopicArn=snstopic,
        Message=message,
        Subject=subject,
    )
    logger.info(f"Notification sent: {response}")
    logger.info(f"notification message: {message}")
