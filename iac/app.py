#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    App,
)

from stack_workshop import WorkShopStack

app = App()

_Stack = WorkShopStack(app, "Stack")

app.synth()
