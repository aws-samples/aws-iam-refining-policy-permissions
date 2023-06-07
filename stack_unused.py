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


class UnusedStack(Stack):
    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            snstopic,
            s3bucket,
            role,
            **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lambda_unused_role_policy = aws_iam.ManagedPolicy(
            self,
            "LambdaUnusedRolePolicy",
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
                    sid="IAMPermissions",
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "iam:GenerateServiceLastAccessedDetails",
                        "iam:GetServiceLastAccessedDetails",
                        "iam:ListRoles"
                    ],
                    resources=[
                        "*"
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

        lambda_unused_role = aws_iam.Role(
            self,
            "LambdaUnusedRole",
            assumed_by=aws_iam.ServicePrincipal(service="lambda.amazonaws.com"),
            managed_policies=[lambda_unused_role_policy],
        )

        lambda_unused_function = aws_lambda.Function(
            self,
            "LambdaUnusedFunction",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=aws_lambda.Code.from_asset("lambda/unused"),
            timeout=Duration.seconds(60),
            role=lambda_unused_role,
            environment={
                "SNS_TOPIC_ARN": snstopic.topic_arn,
                "role_arn": role.role_arn,
                "HoursExpire": "1",
            },

        )

        eventbridge_rule = aws_events.Rule(
            self,
            "EventBridgeRule",
            schedule=aws_events.Schedule.cron(
                minute='10'
            )
        )

        eventbridge_rule.add_target(
            aws_events_targets.LambdaFunction(
                lambda_unused_function,
            )
        )

        CfnOutput(
            self,
            "LambdaUnusedFunctionArn",
            description="ARN for the lambda function performing scanning for unused actions",
            value=lambda_unused_function.function_arn,
        )

        CfnOutput(
            self,
            "EventBridgeRuleArn",
            description="ARN for the EventBridge Rule CRON",
            value=eventbridge_rule.rule_arn,
        )

        CfnOutput(
            self,
            "LambdaUnusedRoleArn",
            description="ARN for the role used by the Lambda function",
            value=eventbridge_rule.rule_arn,
        )

        CfnOutput(
            self,
            "LambdaUnusedRolePolicyArn",
            description="ARN for the role policy used by the Lambda function",
            value=lambda_unused_role_policy.managed_policy_arn,
        )
