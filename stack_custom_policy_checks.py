# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from aws_cdk import (
    Aws,
    BundlingOptions,
    Stack,
    CfnOutput,
    Duration,
    aws_lambda,
    aws_lambda_event_sources,
    aws_iam,
)
from constructs import Construct


class CustomPolicyChecksStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        s3bucket,
        s3key,
        snstopic,
        snsfanoutlambdas,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lambda_custom_policy_checks_role_policy = aws_iam.ManagedPolicy(
            self,
            "LambdaCustomPolicyChecksRolePolicy",
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
                    sid="S3BucketReadPermissions",
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "s3:GetObject",
                    ],
                    resources=[s3bucket.bucket_arn + "/" + s3key],
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
                        "access-analyzer:CheckAccessNotGranted",
                    ],
                    resources=["*"],
                ),
            ],
        )

        lambda_custom_policy_checks_role = aws_iam.Role(
            self,
            "LambdaCustomPolicyChecksRole",
            assumed_by=aws_iam.ServicePrincipal(service="lambda.amazonaws.com"),
            managed_policies=[lambda_custom_policy_checks_role_policy],
        )

        lambda_custom_policy_checks_function = aws_lambda.Function(
            self,
            "LambdaCustomPolicyChecksFunction",
            runtime=aws_lambda.Runtime.PYTHON_3_11,
            handler='lambda_function.lambda_handler',
            code=aws_lambda.Code.from_asset(
                "./lambda/custom_policy_checks/",
                bundling=BundlingOptions(
                    image=aws_lambda.Runtime.PYTHON_3_11.bundling_image,
                    command=[
                        "bash", "-c",
                        "pip install --no-cache -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            ),
            timeout=Duration.seconds(60),
            role=lambda_custom_policy_checks_role,
            environment={
                "SNS_TOPIC_ARN": snstopic.topic_arn,
                "BUCKET":  s3bucket.bucket_name,
                "KEY":  s3key,
            }
        )

        lambda_custom_policy_checks_function.add_event_source(
            aws_lambda_event_sources.SnsEventSource(snsfanoutlambdas)
        )

        CfnOutput(
            self,
            "LambdaCustomPolicyChecksFunctionArn",
            description="ARN for the lambda function performing scanning for custom_policy_checks actions",
            value=lambda_custom_policy_checks_function.function_arn,
        )

        CfnOutput(
            self,
            "LambdaCustomPolicyChecksRolePolicyArn",
            description="ARN for the role policy used by the Lambda function",
            value=lambda_custom_policy_checks_role_policy.managed_policy_arn,
        )