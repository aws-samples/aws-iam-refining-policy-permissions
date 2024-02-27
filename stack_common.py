# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from aws_cdk import (
    Aws,
    Stack,
    BundlingOptions,
    CfnOutput,
    CfnParameter,
    CustomResource,
    Duration,
    aws_accessanalyzer,
    aws_sns,
    aws_s3,
    aws_iam,
    aws_lambda,
    aws_events,
    aws_events_targets,
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

        soft_fail_param = CfnParameter(
            self,
            "SoftFailParam",
            type="String",
            description="Soft fail parameter",
            default="[]",
        )

        hard_fail_param = CfnParameter(
            self,
            "HardFailParam",
            type="String",
            description="Hard fail parameter",
            default="[]",
        )

        sns_topic_name = CfnParameter(
            self,
            "SNSTopicParam",
            type="String",
            description="Name of the SNS Topic for notifications",
            default="IAMAccessAnalyzerFindingNotifications",
        )

        analyzer_name = CfnParameter(
            self,
            "AnalyzerNameParam",
            type="String",
            description="Name of the Analyzer",
            default="workshop-analyzer",
        )

        critical_permissions_file_name = CfnParameter(
            self,
            "CriticalPermissionsFileNameParam",
            type="String",
            description="Name of the file containing the critical permissions list",
            default="permissions.json",
        )

        workshop_participant_role = CfnParameter(
            self,
            "WorkshopParticipantRoleParam",
            type="String",
            description="Name of Workshop Studio Role",
            default="role/WSParticipantRole",
        )

        secops_role_policy = aws_iam.ManagedPolicy(
            self,
            "SecOpsRolePolicy",
            statements=[
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "logs:Describe*",
                    ],
                    resources=[
                        "arn:aws:logs:*:" + Aws.ACCOUNT_ID + ":log-group:*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "iam:Get*",
                        "iam:List*",
                        "iam:PutRolePolicy",
                        "iam:CreatePolicyVersion",
                    ],
                    resources=[
                        "arn:aws:iam::" + Aws.ACCOUNT_ID + ":*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "iam:passrole"
                    ],
                    resources=[
                        "arn:aws:iam::" + Aws.ACCOUNT_ID +":role/WorkshopPipelineStack-IacScanRole*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "access-analyzer:*"
                    ],
                    resources=[
                        "arn:aws:access-analyzer:*:" + Aws.ACCOUNT_ID + ":*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "cloudformation:CreateStack",
                        "cloudformation:DescribeStackEvents",
                        "cloudformation:DescribeStackResources",
                        "cloudformation:GetStackPolicy",
                        "cloudformation:GetTemplate",
                        "cloudformation:ListStackResources"
                    ],
                    resources=[
                        "arn:aws:cloudformation:*:" + Aws.ACCOUNT_ID + ":*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "lambda:Get*",
                        "lambda:List*",
                        "lambda:AddPermission"
                    ],
                    resources=[
                        "*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "sns:Get*",
                        "sns:List*",
                        "sns:ConfirmSubscription",
                        "sns:SetSubscriptionAttributes",
                        "sns:Subscribe"
                    ],
                    resources=[
                        "arn:aws:sns:*:" + Aws.ACCOUNT_ID + ":*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "codepipeline:Get*",
                        "codepipeline:List*"
                    ],
                    resources=[
                        "arn:aws:codepipeline:*:" + Aws.ACCOUNT_ID + ":*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "codebuild:*Get*",
                        "codebuild:List*",
                        "codebuild:UpdateProject",
                        "codebuild:UpdateProjectVisibility",
                    ],
                    resources=[
                        "*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "cloudshell:*"
                    ],
                    resources=[
                        "arn:aws:cloudshell:*:" + Aws.ACCOUNT_ID + ":*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "s3:List*",
                        "s3:GetBucketLocation",
                        "s3:GetBucketAcl",
                        "s3:GetAccountPublicAccessBlock",
                        "s3:GetObject"
                    ],
                    resources=[
                        "arn:aws:s3:::*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "events:Describe*",
                        "events:List*",
                        "events:PutTargets",
                        "events:PutRule"
                    ],
                    resources=[
                        "arn:aws:events:*:" + Aws.ACCOUNT_ID + ":*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "schemas:Describe*",
                        "schemas:List*"
                    ],
                    resources=[
                        "arn:aws:schemas:*:" + Aws.ACCOUNT_ID + ":*"
                    ],
                ),
            ],
        )

        secops_role = aws_iam.Role(
            self,
            "SecOpsRole",
            role_name="SecOpsRole",
            managed_policies=[secops_role_policy],
            assumed_by=aws_iam.AccountPrincipal(
                account_id=Aws.ACCOUNT_ID
            ).with_conditions(
                {"StringEquals": {
                    "aws:PrincipalArn": [
                        "arn:aws:iam::" + Aws.ACCOUNT_ID + ":" + workshop_participant_role.value_as_string
                    ]
                }
                }
            )
        )

        devops_role_policy = aws_iam.ManagedPolicy(
            self,
            "DevOpsRolePolicy",
            statements=[
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "logs:Describe*",
                        "logs:Get*",
                        "logs:List*"
                    ],
                    resources=[
                        "arn:aws:logs:*:" + Aws.ACCOUNT_ID + ":log-group:*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "access-analyzer:*"
                    ],
                    resources=[
                        "arn:aws:access-analyzer:*:" + Aws.ACCOUNT_ID + ":*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "codepipeline:Get*",
                        "codepipeline:List*"
                    ],
                    resources=[
                        "arn:aws:codepipeline:*:" + Aws.ACCOUNT_ID + ":*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "codebuild:*Get*",
                        "codebuild:List*",
                        "codebuild:StartBuild*",
                        "codebuild:RetryBuild*"
                    ],
                    resources=[
                        "*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "codecommit:*Get*",
                        "codecommit:List*",
                        "codecommit:CreateBranch",
                        "codecommit:CreateCommit",
                        "codecommit:CreatePullRequest",
                        "codecommit:UpdateComment",
                        "codecommit:GitPull",
                        "codecommit:GitPush"
                    ],
                    resources=[
                        "arn:aws:codecommit:*:" + Aws.ACCOUNT_ID + ":*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "kms:Encrypt",
                        "kms:Decrypt",
                        "kms:ReEncrypt*",
                        "kms:GenerateDataKey",
                        "kms:GenerateDataKeyWithoutPlaintext",
                        "kms:DescribeKey"
                    ],
                    resources=[
                        "arn:aws:kms:*:" + Aws.ACCOUNT_ID + ":key/*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "cloudshell:*"
                    ],
                    resources=[
                        "*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "s3:List*",
                        "s3:GetBucketLocation",
                        "s3:GetBucketAcl",
                        "s3:GetAccountPublicAccessBlock",
                        "s3:GetObject"
                    ],
                    resources=[
                        "arn:aws:s3:::*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "events:Describe*",
                        "events:List*",
                        "events:PutTargets",
                        "events:PutRule"
                    ],
                    resources=[
                        "arn:aws:events:*:" + Aws.ACCOUNT_ID + ":*"
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "schemas:Describe*",
                        "schemas:List*"
                    ],
                    resources=[
                        "arn:aws:schemas:*:" + Aws.ACCOUNT_ID + ":*"
                    ],
                ),
            ],
        )

        devops_role = aws_iam.Role(
            self,
            "DevOpsRole",
            role_name="DevOpsRole",
            managed_policies=[devops_role_policy],
            assumed_by=aws_iam.AccountPrincipal(
                account_id=Aws.ACCOUNT_ID
            ).with_conditions(
                {"StringEquals": {
                    "aws:PrincipalArn": [
                        "arn:aws:iam::" + Aws.ACCOUNT_ID + ":" + workshop_participant_role.value_as_string
                    ]
                }
                }
            )
        )

        sns_topic = aws_sns.Topic(
            self,
            "SNSTopicNotifications",
            topic_name=sns_topic_name.value_as_string,
        )

        sns_fan_out_lambdas = aws_sns.Topic(
            self,
            "SNSFanOutLambdas",
            topic_name="SNSFanOutLambdas",
        )

        all_purpose_bucket = aws_s3.Bucket(
            self,
            "AllPurposeS3Bucket",
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            encryption=aws_s3.BucketEncryption.S3_MANAGED,
        )

        lambda_custom_resource_role_policy = aws_iam.ManagedPolicy(
            self,
            "LambdaCustomResourceRolePolicy",
            statements=[
                aws_iam.PolicyStatement(
                    sid="AllowSSM",
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "ssm:GetParameter",
                    ],
                    resources=[
                        "arn:aws:ssm:"
                        + Aws.REGION
                        + "::parameter/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2"
                    ],
                ),
                aws_iam.PolicyStatement(
                    sid="AllowS3",
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "s3:PutObject",
                    ],
                    resources=[
                        all_purpose_bucket.bucket_arn,
                        all_purpose_bucket.bucket_arn
                        + "/"
                        + critical_permissions_file_name.value_as_string,
                    ],
                ),
                aws_iam.PolicyStatement(
                    sid="AllowAccessAnalyzer",
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "access-analyzer:CreateAnalyzer",
                    ],
                    resources=[
                        "arn:aws:access-analyzer:*:" + Aws.ACCOUNT_ID + ":analyzer/" + analyzer_name.value_as_string
                    ],
                ),
                aws_iam.PolicyStatement(
                    sid="AllowAccessAnalyzerServiceLinkedRole",
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "iam:CreateServiceLinkedRole",
                    ],
                    resources=[
                        "arn:aws:iam::"+Aws.ACCOUNT_ID + ":role/aws-service-role/access-analyzer.amazonaws.com/AWSServiceRoleForAccessAnalyzer"
                    ],
                ),
            ],
        )

        unused_permissions_role_policy = aws_iam.ManagedPolicy(
            self,
            "UnusedPermissionsRolePolicy",
            managed_policy_name="SEC203",
            statements=[
                aws_iam.PolicyStatement(
                    sid="UnusedPermissions",
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "s3:ListBucket",
                        "ec2:DescribeInstances",
                    ],
                    resources=[
                        "*"
                    ],
                ),
            ],
        )

        lambda_custom_resource_role = aws_iam.Role(
            self,
            "LambdaCustomResourceRole",
            role_name="SEC203",
            managed_policies=[
                unused_permissions_role_policy,
                lambda_custom_resource_role_policy,
                aws_iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ],
            assumed_by=aws_iam.CompositePrincipal(
                aws_iam.ServicePrincipal("lambda.amazonaws.com"),
                aws_iam.AccountPrincipal(account_id=Aws.ACCOUNT_ID)
            )
        )

        lambda_parse_eventbridge_role_policy = aws_iam.ManagedPolicy(
            self,
            "LambdaParseEventBridgeRolePolicy",
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
                    resources=["*"],
                ),
                aws_iam.PolicyStatement(
                    sid="SNSPublishAllow",
                    actions=[
                        "sns:Publish",
                    ],
                    resources=[sns_fan_out_lambdas.topic_arn],
                ),
            ],
        )
        
        lambda_parse_eventbridge_role = aws_iam.Role(
            self,
            "LambdaParseEventBridgeRole",
            assumed_by=aws_iam.ServicePrincipal(service="lambda.amazonaws.com"),
            managed_policies=[lambda_parse_eventbridge_role_policy],
        )

        lambda_function_parse_eventbridge = aws_lambda.Function(
            scope=self,
            id="LambdaFunctionParseEventBridge",
            runtime=aws_lambda.Runtime.PYTHON_3_11,
            handler='lambda_function.lambda_handler',
            role=lambda_parse_eventbridge_role,
            timeout=Duration.seconds(60),
            code=aws_lambda.Code.from_asset(
                "./lambda/common/parse_eventbridge/",
                bundling=BundlingOptions(
                    image=aws_lambda.Runtime.PYTHON_3_11.bundling_image,
                    command=[
                        "bash", "-c",
                        "pip install --no-cache -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            ),
            environment={
                "SNS_TOPIC_ARN": sns_fan_out_lambdas.topic_arn,
            },
        )

        eventbridge_rule = aws_events.Rule(
            self,
            "EventBridgeRule",
            event_pattern=aws_events.EventPattern(
                source=["aws.iam"],
                detail_type=["AWS API Call via CloudTrail"],
                detail={
                    "eventSource": ["iam.amazonaws.com"],
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
                    ],
                },
            ),
        )

        eventbridge_rule.add_target(
            aws_events_targets.LambdaFunction(
                lambda_function_parse_eventbridge,
            ),
        )

        lambda_custom_resource_function = aws_lambda.Function(
            scope=self,
            id="LambdaCustomResourceFunction",
            runtime=aws_lambda.Runtime.PYTHON_3_11,
            handler='lambda_function.lambda_handler',
            role=lambda_custom_resource_role,
            timeout=Duration.seconds(60),
            code=aws_lambda.Code.from_asset(
                "./lambda/common/custom_resource/",
                bundling=BundlingOptions(
                    image=aws_lambda.Runtime.PYTHON_3_11.bundling_image,
                    command=[
                        "bash", "-c",
                        "pip install --no-cache -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            ),
            environment={
                "S3BUCKET": all_purpose_bucket.bucket_name,
                "S3KEY": critical_permissions_file_name.value_as_string
            },
        )

        CustomResource(
            self,
            "CustomResourceLambda",
            service_token=lambda_custom_resource_function.function_arn,
        )

        CfnOutput(
            self,
            "BucketArn",
            description="ARN of the S3 bucket to be used for all purposes",
            value=all_purpose_bucket.bucket_arn,
        )

        CfnOutput(
            self,
            "TopicArn",
            description="ARN of the SNS Topic for notifications",
            value=sns_topic.topic_arn,
        )

        CfnOutput(
            self,
            "DevOpsRoleARN",
            description="ARN for DevOps Role",
            value=devops_role.role_arn,
        )

        CfnOutput(
            self,
            "SecOpsRoleARN",
            description="ARN for SecOps Role",
            value=secops_role.role_arn,
        )

        # CfnOutput(
        #     self,
        #     "AnalyzerARN",
        #     description="ARN for Analyzer",
        #     value=analyzer.attr_arn,
        # )

        self.bucket = all_purpose_bucket
        self.topic = sns_topic
        self.critical_permissions_file_name = critical_permissions_file_name.value_as_string
        self.sns_fan_out_lambdas = sns_fan_out_lambdas
        self.soft_fail_param = soft_fail_param
        self.hard_fail_param = hard_fail_param