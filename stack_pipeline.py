# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from aws_cdk import (
    Aws,
    Stack,
    BundlingOptions,
    Duration,
    aws_iam,
    aws_codebuild,
    aws_codecommit,
    aws_codepipeline,
    aws_codepipeline_actions,
    aws_sns,
    aws_lambda,
    aws_lambda_event_sources,
)
from constructs import Construct


class PipelineStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        snstopic,
        softfailparam,
        hardfailparam,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        code_repository = aws_codecommit.Repository(
            self,
            "CodeRepository",
            repository_name="workshop_repo",
            code=aws_codecommit.Code.from_directory("iac", "main"),
        )

        iac_scan = aws_codebuild.Project(
            self,
            "IacScan",
            environment=aws_codebuild.BuildEnvironment(
                privileged=True,
                build_image=aws_codebuild.LinuxBuildImage.AMAZON_LINUX_2_5,
                environment_variables={
                    "AWS_REGION": aws_codebuild.BuildEnvironmentVariable(
                        value=Aws.REGION
                    ),
                    "AWS_ACCOUNT_ID": aws_codebuild.BuildEnvironmentVariable(
                        value=Aws.ACCOUNT_ID
                    ),
                    "SOFT_FAIL": aws_codebuild.BuildEnvironmentVariable(
                        value=softfailparam.value_as_string
                    ),
                    "HARD_FAIL": aws_codebuild.BuildEnvironmentVariable(
                        value=hardfailparam.value_as_string
                    ),
                },
            ),
            source=aws_codebuild.Source.code_commit(
                repository=code_repository, branch_or_ref="main"
            ),
            build_spec=aws_codebuild.BuildSpec.from_object(
                {
                    "version": "0.1",
                    "phases": {
                        "install": {
                            "commands": [
                                "npm i",
                                "npm install -g aws-cdk",
                                "npx cdk version",
                                "python -m venv .venv",
                                ". .venv/bin/activate",
                                "python --version",
                                "pip install -r requirements.txt",
                                "pip install cfn-policy-validator",
                            ]
                        },
                        "build": {
                            "commands": [
                                "npx cdk synth > ./iac.yaml",
                                "echo 'call cfn-policy-validator to extract policies and roles'",
                                "cfn-policy-validator parse --template-path ./iac.yaml --region ${AWS_REGION} > iac_iam_parsed.json",
                                "cat iac_iam_parsed.json | jq -r '.Roles[].Policies[].Policy' > policy.json",
                                "echo 'call access analyzer to validate policy'",
                                ## add your commands here 
                                "echo 'call custom policy checks'",
                                ## add your commands here
                            ]  
                        },  
                    },  
                }
            ),
        )

        code_repository.grant_pull(iac_scan)

        iac_scan.add_to_role_policy(
            aws_iam.PolicyStatement(
                actions=[
                    "iam:GetPolicy",
                    "iam:GetPolicyVersion",
                    "access-analyzer:ListAnalyzers",
                    "access-analyzer:ValidatePolicy",
                    "access-analyzer:CreateAccessPreview",
                    "access-analyzer:GetAccessPreview",
                    "access-analyzer:ListAccessPreviewFindings",
                    "access-analyzer:CreateAnalyzer",
                    "access-analyzer:CheckAccessNotGranted",
                    "s3:ListAllMyBuckets",
                    "cloudformation:ListExports",
                    "ssm:GetParameter",
                ],
                resources=["*"],
                effect=aws_iam.Effect.ALLOW,
            ),
        )

        iac_scan.add_to_role_policy(
            aws_iam.PolicyStatement(
                actions=[
                    "iam:CreateServiceLinkedRole",
                ],
                resources=["*"],
                effect=aws_iam.Effect.ALLOW,
                conditions={
                    "StringEquals": {
                        "iam:AWSServiceName": "access-analyzer.amazonaws.com"
                    }
                },
            )
        )

        sns_pipeline = aws_sns.Topic(
            self,
            "SNSPipeline",
            topic_name="SNSPipeline",
        )

        iac_scan.add_to_role_policy(
            aws_iam.PolicyStatement(
                sid="SNSPublishAllow",
                actions=[
                    "sns:Publish",
                ],
                resources=[sns_pipeline.topic_arn],
            )
        )

        lambda_pipeline_notification_role_policy = aws_iam.ManagedPolicy(
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
                    sid="SNSPublishAllow",
                    actions=[
                        "sns:Publish",
                    ],
                    resources=[snstopic.topic_arn],
                )
            ]
        )

        lambda_pipeline_notification_role = aws_iam.Role(
            self,
            "LambdaParseEventBridgeRole",
            assumed_by=aws_iam.ServicePrincipal(service="lambda.amazonaws.com"),
            managed_policies=[lambda_pipeline_notification_role_policy],
        )

        lambda_function_pipeline_notification = aws_lambda.Function(
            scope=self,
            id="LambdaFunctionPipelineNotication",
            runtime=aws_lambda.Runtime.PYTHON_3_11,
            handler='lambda_function.lambda_handler',
            role=lambda_pipeline_notification_role,
            timeout=Duration.seconds(60),
            code=aws_lambda.Code.from_asset(
                "./lambda/pipeline/",
                bundling=BundlingOptions(
                    image=aws_lambda.Runtime.PYTHON_3_11.bundling_image,
                    command=[
                        "bash", "-c",
                        "pip install --no-cache -r requirements.txt -t /asset-output && cp -au . /asset-output"
                    ]
                )
            ),
            environment={
                "SNS_TOPIC_ARN": snstopic.topic_arn,
            },
        )

        lambda_function_pipeline_notification.add_event_source(
            aws_lambda_event_sources.SnsEventSource(
                sns_pipeline)
        )

        source_artifact = aws_codepipeline.Artifact("SourceArtifact")
        build_artifact = aws_codepipeline.Artifact("BuildArtifact")

        source_stage = aws_codepipeline.StageProps(
            stage_name="Source",
            actions=[
                aws_codepipeline_actions.CodeCommitSourceAction(
                    action_name="CodeCommit",
                    branch="main",
                    output=source_artifact,
                    repository=code_repository,
                )
            ],
        )

        build_stage = aws_codepipeline.StageProps(
            stage_name="Build",
            actions=[
                aws_codepipeline_actions.CodeBuildAction(
                    action_name="IacScan",
                    input=aws_codepipeline.Artifact("SourceArtifact"),
                    project=iac_scan,
                    outputs=[build_artifact],
                )
            ],
        )

        iac_scan_pipeline = aws_codepipeline.Pipeline(
            self,
            "IacScanPipeline",
            stages=[source_stage, build_stage],
        )

        self.iacscan = iac_scan
        self.snspipeline = sns_pipeline