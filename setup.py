# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
import setuptools

AWS_CDK_VERSION = "2.110.0"

setuptools.setup(
    name="aws-iam-refining-policy-permissions",
    version="1",
    description="re:Invent 2023",
    author="AWS",
    package_dir={"": "."},
    packages=setuptools.find_packages(where="."),
    install_requires=[
        "aws-cdk-lib==" + AWS_CDK_VERSION,
    ],
    python_requires=">=3.11",
    classifiers=[
        "Development Status :: Proof of concept",
        "Intended Audience :: DevSecOps",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
    ],
)
