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
    response = ""
    client_sns = boto3.client("sns")
    for analyzer in event["resources"]:
        logger.info(f"### finding id {findind_id} analyzer {analyzer}")
        response = client_accessanalyzer.get_finding_v2(
            analyzerArn=analyzer,
            id=findind_id,
        )
        logger.info(f"### Response {response}")
        account = event["detail"]["accountId"]
        principal = event["detail"]["resource"]
        finding_type = event["detail"]["findingType"]
        analysis_time = event["detail"]["analyzedAt"]
        unused_services = event["detail"]["numberOfUnusedServices"]
        unused_actions = event["detail"]["numberOfUnusedActions"]
        last_used = ""
        for detail in response["findingDetails"]:
            if "unusedIamRoleDetails" in detail:
                last_used = detail["unusedIamRoleDetails"]["lastAccessed"]
                logger.info(f"### last used {last_used}")
        message = (
            f"Unused Findings for account {account} on analyzer {analyzer} \n\n"
            f"Principal: {principal} \n\n"
            f"Finding type: {finding_type} \n\n"
            f"Analysed at: {analysis_time} \n\n"
            f"Number of unused services {unused_services} and actions {unused_actions} \n\n"
            f"Last used: {last_used} \n\n"
        )
        subject = "Unused access findings"
        response = client_sns.publish(
            TopicArn=snstopic,
            Message=message,
            Subject=subject,
        )
        logger.info(f"Notification sent: {response}")
        logger.info(f"notification message: {message}")
