# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from aws_cdk import (
    Aws,
    Stack,
    aws_iam,
)

from constructs import Construct


class WorkShopStack(Stack):
    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lambda_role_policy = aws_iam.ManagedPolicy(
            self,
            "WorkshopRolePolicy",
            statements=[
                aws_iam.PolicyStatement(
                    sid="CloudWatchLogsWritePermissions",
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                    ],
                    resources=[
                        "arn:aws:logs:" + Aws.REGION + ":" + Aws.ACCOUNT_ID + ":log-group:/*"
                    ],
                ),
            ]
        )

        lambda_role = aws_iam.Role(
            self,
            "LambdaRole",
            assumed_by=aws_iam.ServicePrincipal(service="lambda.amazonaws.com"),
            managed_policies=[lambda_role_policy],
        )


