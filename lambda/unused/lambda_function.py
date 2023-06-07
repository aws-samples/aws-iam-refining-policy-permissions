"""Gathers information on roles access history."""
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
import time
from datetime import datetime
import json
import os
import random
import logging

sns_topic_arn = os.environ["SNS_TOPIC_ARN"]
# Services that Support action level tracking
ACTION_LEVEL = ['s3', 'ec2', 'iam', 'lambda']

LOGGER = logging.getLogger()
logging.basicConfig(
    format="[%(asctime)s] %(levelname)s [%(module)s.%(funcName)s:%(lineno)d] %(message)s", datefmt="%H:%M:%S"
)
LOGGER.setLevel(logging.INFO)

config = Config(
   retries = {
      'max_attempts': 10,
      'mode': 'standard'
   }
)
client_iam = boto3.client("iam", config=config)
client_sns = boto3.client("sns")


def generate_service_last_accessed_details(arn, client):
    """Generate reports."""
    while True:
        try:
            response = client.generate_service_last_accessed_details(
                Arn=arn,
                Granularity='ACTION_LEVEL'
            )
            break
        except ClientError as error:
            LOGGER.error('Generate report for entity %s failed with error : %s', arn, error)
    return response['JobId']

def get_service_last_accessed_details(job_id, entity, client):
    """Get entity access details."""
    role_info = []
    marker = ''

    while marker is not None:
        if marker == '':
            try:
                response = client.get_service_last_accessed_details(
                    JobId=job_id
                )
                assert response['JobStatus'] == 'COMPLETED'
            except AssertionError as error:
                if response['JobStatus'] == 'FAILED':
                    LOGGER.error('Entity %s job FAILED with error: %s', entity, error)
                    break
                continue
            except ClientError as error:
                LOGGER.error('Client Error message on get: %s', error)

            role_info += response['ServicesLastAccessed']
            marker = response.get('Marker', None)
        else:
            try:
                response = client.get_service_last_accessed_details(
                    JobId=job_id,
                    Marker=marker
                )
            except ClientError as error:
                LOGGER.error('Client Error message on get: %s', error)

            role_info += response['ServicesLastAccessed']
            marker = response.get('Marker', None)
    return role_info


def calculate_service(service):
    """
    Calculate service usage.
    """
    # Determine if service has been access by the entity
    if int(service['TotalAuthenticatedEntities']) > 0:

        # Get time when user last authenticated to the services
        time_gap = datetime.today() - service['LastAuthenticated'].replace(tzinfo=None)

        # service not used within expiration period
        if int(time_gap.total_seconds() / 3600) > int(os.environ['HoursExpire']):
            return True
        else:
            return False
    else:
        return True


def calculate_actions(service):
    """Calculate action level for services that support it."""
    action_list = {
        'ServiceName': service['ServiceName'],
        'ServiceNamespace': service['ServiceNamespace'],
        'Actions': []
    }
    # Make sure there is action level history
    if 'TrackedActionsLastAccessed' in service.keys():
        for action in service['TrackedActionsLastAccessed']:
            if 'LastAccessedTime' in action.keys():
                # Get time when user last authenticated to the services
                time_gap = datetime.today() - service['LastAuthenticated'].replace(tzinfo=None)
                # service not used within expiration period
                if int(time_gap.total_seconds() / 3600) > int(os.environ['HoursExpire']):
                    action_list['Actions'].append(action['ActionName'])
            else:
                action_list['Actions'].append(action['ActionName'])
        return action_list

    # Service that Supports Action level has no access history
    else:
        action_list['Actions'].append('All Actions')
        return action_list


def build_service_level(service):
    """
    Build service item.
    """
    action_list = {
        'ServiceName': service['ServiceName'],
        'ServiceNamespace': service['ServiceNamespace']
    }
    return action_list


def analyze_entities(entity):
    result = {}

    LOGGER.info('Starting evaluation: %s', entity)

    job_id = generate_service_last_accessed_details(entity, client_iam)
    details = get_service_last_accessed_details(job_id, entity, client_iam)
    
    expired_services = []
    for service in details:
        if service['ServiceNamespace'] in ACTION_LEVEL:
            service_actions = calculate_actions(service)
            if service_actions['Actions']:
                expired_services.append(service_actions)
        else:
            if calculate_service(service):
                expired_services.append(build_service_level(service))

    if expired_services:
        _, name = entity.rsplit('/', 1)
        result = {
            "EntityARN": entity,
            "EntityName": name,
            "TotalServices": len(details),
            "ExpiredServices": len(expired_services),
            "ExpiredServiceList": expired_services
        }
        LOGGER.info('End evaluation: %s', entity)
        return result

    LOGGER.info('End evaluation: %s', entity)
    return None


def lambda_handler(event, context):
    """Start Function."""
    LOGGER.info('Start Evaluation...')
    entity = os.environ['role_arn']
    result = analyze_entities(entity)
    LOGGER.info(json.dumps(result, indent=2))
    if result:
        message = (
            f"Unused Permissions: {json.dumps(result, indent=4)}"
        )
        subject = "Policy Document contains unused permission(s)"
        client_sns.publish(
            TopicArn=sns_topic_arn,
            Message=message,
            Subject=subject,
        )
        LOGGER.info("Notification sent")
        LOGGER.info(message)
    LOGGER.info('End Evaluation...')
