#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    App,
)

from stack_common import CommonStack
from stack_custom_policy_checks import CustomPolicyChecksStack
from stack_unused_access import UnusedAccessStack
from stack_policy_validator import PolicyValidatorStack
from stack_pipeline import PipelineStack
from stack_pipeline_notification import PipelineNotificationStack
app = App()

_CommonStack = CommonStack(
    app,
    "CommonStack",
    stack_name="WorkshopCommonStack"
)
_CustomPolicyChecksStack = CustomPolicyChecksStack(
    app,
    "CustomPolicyChecksStack",
    stack_name="WorkshopCustomPolicyChecksStack",
    s3bucket=_CommonStack.bucket,
    s3key=_CommonStack.critical_permissions_file_name,
    snstopic=_CommonStack.topic,
    snsfanoutlambdas=_CommonStack.sns_fan_out_lambdas,
)
_PolicyValidatorStack = PolicyValidatorStack(
    app,
    "PolicyValidatorStack",
    stack_name="WorkshopPolicyValidatorStack",
    snstopic=_CommonStack.topic,
    snsfanoutlambdas=_CommonStack.sns_fan_out_lambdas,
    softfailparam=_CommonStack.soft_fail_param,
    hardfailparam=_CommonStack.hard_fail_param,
)
_UnusedAccessStack = UnusedAccessStack(
    app,
    "UnusedAccessStack",
    stack_name="WorkshopUnusedAccessStack",
    snstopic=_CommonStack.topic,
)
_PipelineStack = PipelineStack(
    app,
    "PipelineStack",
    stack_name="WorkshopPipelineStack",
    snstopic=_CommonStack.topic,
    softfailparam=_CommonStack.soft_fail_param,
    hardfailparam=_CommonStack.hard_fail_param,
)
_PipelineNotificationStack = PipelineNotificationStack(
    app,
    "PipelineNotificationStack",
    stack_name="WorkshopNotificationPipelineStack",
    snspipeline=_PipelineStack.snspipeline,
    iacscan=_PipelineStack.iacscan,
)

app.synth()
