# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from aws_cdk import (
    Aws,
    Stack,
    CfnOutput,
    Duration,
    aws_lambda,
    aws_lambda_event_sources,
    aws_iam,
    BundlingOptions,
)
from constructs import Construct


class PolicyValidatorStack(Stack):
    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            snstopic,
            snsfanoutlambdas,
            softfailparam,
            hardfailparam,
            **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lambda_policy_validator_role_policy = aws_iam.ManagedPolicy(
            self,
            "LambdaPolicyValidatorRolePolicy",
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
                    actions=[
                        "access-analyzer:ValidatePolicy",
                    ],
                    resources=["*"],
                    effect=aws_iam.Effect.ALLOW,
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

        lambda_policy_validator_role = aws_iam.Role(
            self,
            "LambdaPolicyValidatorRole",
            assumed_by=aws_iam.ServicePrincipal(service="lambda.amazonaws.com"),
            managed_policies=[lambda_policy_validator_role_policy],
        )

        lambda_policy_validator_function = aws_lambda.Function(
            self,
            "LambdaPolicyValidatorFunction",
            runtime=aws_lambda.Runtime.PYTHON_3_11,
            handler="lambda_function.lambda_handler",
            timeout=Duration.seconds(60),
            role=lambda_policy_validator_role,
            code=aws_lambda.Code.from_asset(
                "./lambda/policy_validator/",
                bundling=BundlingOptions(
                    image=aws_lambda.Runtime.PYTHON_3_11.bundling_image,
                    command=[
                        "bash", "-c",
                        "pip install --no-cache -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            ),
            environment={
                "REGION": str(Aws.REGION),
                "ACCOUNT_ID": str(Aws.ACCOUNT_ID),
                "SNS_TOPIC_ARN": snstopic.topic_arn,
                "SOFT_FAIL": softfailparam.value_as_string,
                "HARD_FAIL": hardfailparam.value_as_string,
            },
        )

        lambda_policy_validator_function.add_event_source(
            aws_lambda_event_sources.SnsEventSource(
                snsfanoutlambdas)
        )

        CfnOutput(
            self,
            "LambdaPolicyValidatorFunctionArn",
            description="ARN for the lambda function performing scanning for privileged actions",
            value=lambda_policy_validator_function.function_arn,
        )

        CfnOutput(
            self,
            "LambdaPolicyValidatorRolePolicyArn",
            description="ARN for the role policy used by the Lambda function",
            value=lambda_policy_validator_role_policy.managed_policy_arn,
        )