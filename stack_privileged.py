# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from aws_cdk import (
    Aws,
    Stack,
    CfnOutput,
    Duration,
    aws_lambda,
    aws_iam,
    aws_events,
    aws_events_targets
)
from constructs import Construct


class PrivilegedStack(Stack):
    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            snstopic,
            s3bucket,
            **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lambda_privileged_role_policy = aws_iam.ManagedPolicy(
            self,
            "LambdaPrivilegedRolePolicy",
            statements=[
                aws_iam.PolicyStatement(
                    sid="CloudWatchLogsWritePermissions",
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    resources=[
                        "arn:aws:logs:" + Aws.REGION + ":" + Aws.ACCOUNT_ID + ":log-group:/*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    sid="IAMReadPermissions",
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "iam:GetGroupPolicy",
                        "iam:GetRolePolicy",
                        "iam:GetUserPolicy",
                        "iam:GetPolicyVersion",
                        "iam:GetPolicy",
                    ],
                    resources=[
                        "*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    sid="S3BucketReadPermissions",
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "s3:GetObject",
                    ],
                    resources=[
                       s3bucket.bucket_arn + "/privileged.txt",
                    ],
                ),
                aws_iam.PolicyStatement(
                    sid="SNSPublishAllow",
                    actions=[
                        "sns:Publish",
                    ],
                    resources=[snstopic.topic_arn],
                )
            ]
        )

        lambda_privileged_role = aws_iam.Role(
            self,
            "LambdaPrivilegedRole",
            assumed_by=aws_iam.ServicePrincipal(service="lambda.amazonaws.com"),
            managed_policies=[lambda_privileged_role_policy],
        )

        lambda_privileged_function = aws_lambda.Function(
            self,
            "LambdaPrivilegedFunction",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=aws_lambda.Code.from_asset("lambda/privileged"),
            timeout=Duration.seconds(60),
            role=lambda_privileged_role,
            environment={
                "BUCKET": s3bucket.bucket_name,
                "KEY": "privileged.txt",
                "SNS_TOPIC_ARN": snstopic.topic_arn,
            },

        )

        eventbridge_rule = aws_events.Rule(
            self,
            "EventBridgeRule",
            event_pattern=aws_events.EventPattern(
                source=["aws.iam"],
                detail_type=["AWS API Call via CloudTrail"],
                detail={"eventSource": [
                    "iam.amazonaws.com"
                ],
                    "eventName": [
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
                }
            )
        )

        eventbridge_rule.add_target(
            aws_events_targets.LambdaFunction(
                lambda_privileged_function,
            )
        )

        CfnOutput(
            self,
            "LambdaPrivilegedFunctionArn",
            description="ARN for the lambda function performing scanning for privileged actions",
            value=lambda_privileged_function.function_arn,
        )

        CfnOutput(
            self,
            "EventBridgeRuleArn",
            description="ARN for the EventBridge Rule detecting IAM policy changes",
            value=eventbridge_rule.rule_arn,
        )

        CfnOutput(
            self,
            "LambdaPrivilegedRoleArn",
            description="ARN for the role used by the Lambda function",
            value=eventbridge_rule.rule_arn,
        )

        CfnOutput(
            self,
            "LambdaPrivilegedRolePolicyArn",
            description="ARN for the role policy used by the Lambda function",
            value=lambda_privileged_role_policy.managed_policy_arn,
        )
