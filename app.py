#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    App,
)

from stack_common import CommonStack
from stack_privileged import PrivilegedStack
from stack_unused import UnusedStack

app = App()

_CommonStack = CommonStack(app, "CommonStack")
_PrivilegedStack = PrivilegedStack(
    app,
    "PrivilegedStack",
    snstopic=_CommonStack.topic,
    s3bucket=_CommonStack.bucket
)
_UnusedStack = UnusedStack(
    app,
    "UnusedStack",
    snstopic=_CommonStack.topic,
    s3bucket=_CommonStack.bucket,
    role=_CommonStack.role,
)

app.synth()
