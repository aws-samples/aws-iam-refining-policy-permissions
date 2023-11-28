"""Gathers information on roles access history."""
import boto3
import logging
import os
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)

snstopic = os.environ["SNS_TOPIC_ARN"]

client_accessanalyzer = boto3.client("accessanalyzer")

def lambda_handler(event, context):
    """Lambda Handler"""
    logger.info(f"### event received {event}")
    findind_id = event["detail"]["findingId"]
    analyzer = event["detail"]["resource"]
    response = ""
    client_sns = boto3.client("sns")
    logger.info(f"### finding id {findind_id} analyzer {analyzer}")
    response = client_accessanalyzer.get_finding_v2(
        analyzerArn=analyzer,
        id=findind_id,
    )
    logger.info(f"### Response {response}")
    status = response["status"]
    created_at = response["createdAt"]
    resource_type = response["resourceType"]
    finding_type = response["findingType"]
    resource_owner_account = response["resourceOwnerAccount"]
    analysis_time = response["analyzedAt"]
    findind_id = response["id"]
    updated_at = response["updatedAt"]
    finding_details = response["findingDetails"]
    message = (
        f"Analyzer {analyzer} \n\n"
        f"Finding id {findind_id} \n\n"
        f"Status: {status} \n\n"
        f"Created at: {created_at} \n\n"
        f"Resource Type: {resource_type} \n\n"
        f"Finding Type: {finding_type} \n\n"
        f"Resource Owner Account: {resource_owner_account} \n\n"
        f"Analysis Time: {analysis_time} \n\n"
        f"Finding ID: {findind_id} \n\n"
        f"Updated at: {updated_at} \n\n"
        f"Finding Details: {finding_details} \n\n"
    )
    subject = "Unused findings"
    response = client_sns.publish(
        TopicArn=snstopic,
        Message=message,
        Subject=subject,
    )
    logger.info(f"Notification sent: {response}")
    logger.info(f"notification message: {message}")
