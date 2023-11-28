# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from aws_cdk import (
    Aws,
    BundlingOptions,
    Stack,
    CfnOutput,
    Duration,
    aws_lambda,
    aws_iam,
)
from constructs import Construct


class UnusedAccessStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, snstopic, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lambda_unused_access_role_policy = aws_iam.ManagedPolicy(
            self,
            "LambdaUnusedAccessRolePolicy",
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
                        "arn:aws:logs:"
                        + Aws.REGION
                        + ":"
                        + Aws.ACCOUNT_ID
                        + ":log-group:/*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    sid="IAMPermissions",
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "iam:GenerateServiceLastAccessedDetails",
                        "iam:GetServiceLastAccessedDetails",
                        "iam:ListRoles",
                    ],
                    resources=["*"],
                ),
                aws_iam.PolicyStatement(
                    sid="SNSPublishAllow",
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "sns:Publish",
                    ],
                    resources=[snstopic.topic_arn],
                ),
                aws_iam.PolicyStatement(
                    sid="AccessAnalyzerPermissions",
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "access-analyzer:GetFinding",
                    ],
                    resources=["*"],
                ),
            ],
        )

        lambda_unused_access_role = aws_iam.Role(
            self,
            "LambdaUnusedAccessRole",
            assumed_by=aws_iam.ServicePrincipal(service="lambda.amazonaws.com"),
            managed_policies=[lambda_unused_access_role_policy],
        )

        lambda_unused_access_function = aws_lambda.Function(
            self,
            "LambdaUnusedAccessFunction",
            runtime=aws_lambda.Runtime.PYTHON_3_11,
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset(
                "./lambda/unused_access/",
                bundling=BundlingOptions(
                    image=aws_lambda.Runtime.PYTHON_3_11.bundling_image,
                    command=[
                        "bash", "-c",
                        "pip install --no-cache -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            ),
            timeout=Duration.seconds(60),
            role=lambda_unused_access_role,
            environment={
                "SNS_TOPIC_ARN": snstopic.topic_arn,
            },
        )

        CfnOutput(
            self,
            "LambdaUnusedAccessFunctionArn",
            description="ARN for the lambda function performing scanning for unused_access actions",
            value=lambda_unused_access_function.function_arn,
        )

        CfnOutput(
            self,
            "LambdaUnusedAccessRolePolicyArn",
            description="ARN for the role policy used by the Lambda function",
            value=lambda_unused_access_role_policy.managed_policy_arn,
        )
