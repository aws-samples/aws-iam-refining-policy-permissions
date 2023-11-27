# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from aws_cdk import (
    Stack,
    aws_codestarnotifications,
)
from constructs import Construct


class PipelineNotificationStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        snspipeline,
        iacscan,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        pipeline_notification = aws_codestarnotifications.NotificationRule(
            self,
            "PipelineNotification",
            source=iacscan,
            events=[
                "codebuild-project-build-state-succeeded",
                "codebuild-project-build-state-failed",
            ],
            targets=[snspipeline],
            detail_type=aws_codestarnotifications.DetailType.BASIC,
            enabled=True,
        )
