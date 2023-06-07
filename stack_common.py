# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from aws_cdk import (
    Aws,
    Stack,
    BundlingOptions,
    CfnParameter,
    CustomResource,
    Duration,
    aws_sns,
    aws_s3,
    aws_iam,
    aws_lambda,
)

from constructs import Construct


class CommonStack(Stack):
    def __init__(
            self,
            scope: Construct,
            construct_id: str,
            **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        sns_topic_name = CfnParameter(
            self,
            "SNSTopicParam",
            type="String",
            description="Name of the SNS Topic for notifications",
            default="PrivilegeFindingNotifications",
        )

        sns_topic = aws_sns.Topic(
            self,
            "SNSTopicNotifications",
            topic_name=sns_topic_name.value_as_string,
        )

        all_purpose_bucket = aws_s3.Bucket(
            self,
            "AllPurposeS3Bucket",
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            encryption=aws_s3.BucketEncryption.S3_MANAGED,
        )

        workshop_role_policy = aws_iam.ManagedPolicy(
            self,
            "WorkshopRolePolicy",
            statements=[
                aws_iam.PolicyStatement(
                    sid="AllowS3",
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "s3:*",
                    ],
                    resources=["*"]
                ),
                aws_iam.PolicyStatement(
                    sid="AllowEC2",
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "ec2:*",
                    ],
                    resources=["*"]
                ),
            ]
        )

        workshop_role = aws_iam.Role(
            self,
            "WorkShopRole",
            role_name="IAM354",
            managed_policies=[
                workshop_role_policy,
                aws_iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            assumed_by=aws_iam.CompositePrincipal(
                aws_iam.ServicePrincipal("lambda.amazonaws.com"),
                aws_iam.AccountPrincipal(account_id=Aws.ACCOUNT_ID)
            )
        )

        lambda_function = aws_lambda.Function(
            scope=self,
            id="LambdaFunction",
            runtime=aws_lambda.Runtime.PYTHON_3_9,
            handler='lambda_function.lambda_handler',
            role=workshop_role,
            timeout=Duration.seconds(60),
            code=aws_lambda.Code.from_asset(
                "./lambda/common/",
                bundling=BundlingOptions(
                    image=aws_lambda.Runtime.PYTHON_3_9.bundling_image,
                    command=[
                        "bash", "-c",
                        "pip install --no-cache -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            ),
            environment={
                "REGION": str(Aws.REGION),
                "S3BUCKET": all_purpose_bucket.bucket_name,
                "S3KEY": "privileged.txt"
            },
        )

        CustomResource(
            self,
            "CustomResourceLambda",
            service_token=lambda_function.function_arn,
        )

        self.bucket = all_purpose_bucket
        self.topic = sns_topic
        self.role = workshop_role
