import boto3
import cfnresponse
import logging
import os
import json
import traceback
import sys

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3bucket = os.environ["S3BUCKET"]
s3key = os.environ["S3KEY"]

client_s3 = boto3.client("s3")
client_accessanalyzer = boto3.client("accessanalyzer")

privileged_actions = [
    "cloudtrail:DeleteTrail",
    "cloudtrail:PutEventSelectors",
    "cloudtrail:StopLogging",
    "cloudtrail:UpdateTrail",
    "ec2:AcceptVpcPeeringConnection",
    "ec2:AssociateAddress",
    "ec2:AssociateDhcpOptions",
    "ec2:AssociateIamInstanceProfile",
    "ec2:AttachInternetGateway",
    "ec2:AssociateRouteTable",
    "ec2:AttachVpnGateway",
    "ec2:CreateKeyPair",
    "ec2:CreateNetworkAclEntry",
    "ec2:CreateRoute",
    "ec2:CreateVpcEndpoint",
    "ec2:CreateVpcPeeringConnection",
    "ec2:CreateVpnConnection",
    "ec2:CreateVpnConnectionRoute",
    "ec2:DeleteNetworkAcl",
    "ec2:DeleteNetworkAclEntry",
    "ec2:DeleteVpnConnectionRoute",
    "ec2:DisassociateRouteTable",
    "ec2:DisableVgwRoutePropagation",
    "ec2:EnableVgwRoutePropagation",
    "ec2:ImportKeyPair",
    "ec2:ModifySubnetAttribute",
    "ec2:ModifyVpcEndpoint",
    "ec2:PurchaseReservedInstancesOffering",
    "ec2:ReplaceNetworkAclAssociation",
    "ec2:ReplaceNetworkAclEntry",
    "ec2:ReplaceRoute",
    "ec2:ReplaceRouteTableAssociation",
    "iam:AddRoleToInstanceProfile",
    "iam:AddUserToGroup",
    "iam:AttachGroupPolicy",
    "iam:AttachRolePolicy",
    "iam:AttachUserPolicy",
    "iam:CreateAccountAlias",
    "iam:CreatePolicy",
    "iam:CreatePolicyVersion",
    "iam:CreateRole",
    "iam:CreateSAMLProvider",
    "iam:CreateUser",
    "iam:DeleteAccountPasswordPolicy",
    "iam:DeleteGroupPolicy",
    "iam:DeletePolicy",
    "iam:DeletePolicyVersion",
    "iam:DeleteRolePolicy",
    "iam:DeleteUserPolicy",
    "iam:DetachGroupPolicy",
    "iam:DetachRolePolicy",
    "iam:DetachUserPolicy",
    "iam:PassRole",
    "iam:PutGroupPolicy",
    "iam:PutRolePolicy",
    "iam:PutUserPolicy",
    "iam:RemoveRoleFromInstanceProfile",
    "iam:RemoveUserFromGroup",
    "iam:SetDefaultPolicyVersion",
    "iam:UpdateAccountPasswordPolicy",
    "iam:UpdateAssumeRolePolicy",
    "iam:UpdateGroup",
    "iam:UpdateSAMLProvider",
    "iam:UpdateUser",
    "organizations:AcceptHandshake",
    "organizations:CreateAccount",
    "organizations:DeletePolicy",
    "organizations:DetachPolicy",
    "organizations:InviteAccountToOrganization",
    "organizations:LeaveOrganization",
    "organizations:MoveAccount",
    "organizations:RemoveAccountFromOrganization",
    "organizations:UpdatePolicy",
    "s3:PutBucketVersioning",
]


def lambda_handler(event, context):
    logger.info(f"### RAW Event {json.dumps(event)}")
    with open(r"/tmp/" + s3key, "w") as fp:
        fp.write("\n".join(str(item) for item in privileged_actions))
    client_s3.upload_file("/tmp/" + s3key, s3bucket, s3key)
    try:
        result = client_accessanalyzer.create_analyzer(
            analyzerName="workshop-analyzer",
            configuration={"unusedAccess": {"unusedAccessAge": 1}},
            type="ACCOUNT_UNUSED_ACCESS",
        )
        logger.info(f"### Result {json.dumps(result, indent=4)}")
    except Exception as _exp:
        exception_type, exception_value, exception_traceback = sys.exc_info()
        logger.error(
            json.dumps(
                {
                    "errorType": exception_type.__name__,
                    "errorMessage": str(exception_value),
                    "stackTrace": traceback.format_exception(
                        exception_type, exception_value, exception_traceback
                    ),
                },
                indent=4,
            )
        )
    cfnresponse.send(event, context, cfnresponse.SUCCESS, {"Response": "Success"})