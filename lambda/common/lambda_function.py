import json
import boto3
import cfnresponse
import logging
import os
import traceback
import sys

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

ec2_ami = {
    "ap-south-1": "ami-04bde106886a53080",
    "ap-northeast-1": "ami-0fe22bffdec36361c",
    "ap-northeast-2": "ami-0ba5cd124d7a79612",
    "ap-northeast-3": "ami-092faff259afb9a26",
    "ap-southeast-1": "ami-055147723b7bca09a",
    "ap-southeast-2": "ami-0f39d06d145e9bb63",
    "ca-central-1": "ami-0e28822503eeedddc",
    "eu-central-1": "ami-0b1deee75235aa4bb",
    "eu-west-1": "ami-0943382e114f188e8",
    "eu-west-2": "ami-09a56048b08f94cdf",
    "eu-west-3": "ami-06602da18c878f98d",
    "eu-north-1": "ami-0afad43e7d620260c",
    "sa-east-1": "ami-05aa753c043f1dcd3",
    "us-east-1": "ami-0747bdcabd34c712a",
    "us-east-2": "ami-00399ec92321828f5",
    "us-west-1": "ami-07b068f843ec78e72",
    "us-west-2": "ami-090717c950a5c34d3",
}

with open(r'/tmp/privileged.txt', 'w') as fp:
    fp.write("\n".join(str(item) for item in privileged_actions))


def lambda_handler(event, context):
    region = os.environ["REGION"]
    s3bucket = os.environ["S3BUCKET"]
    s3key = os.environ["S3KEY"]
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.info(json.dumps(event))
    client_s3 = boto3.client("s3")
    client_ec2 = boto3.client("ec2")
    client_s3.list_buckets()
    client_s3.upload_file(
        "/tmp/privileged.txt",
        s3bucket,
        s3key
    )
    client_s3.get_object(Bucket=s3bucket, Key=s3key)
    client_s3.generate_presigned_url(
        "get_object", Params={"Bucket": s3bucket, "Key": s3key}, ExpiresIn=60
    )
    try:
        client_ec2.run_instances(
            ImageId=ec2_ami[region],
            InstanceType="t3.micro",
            DryRun=True,
            MinCount=1,
            MaxCount=3
        )
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
                indent=4
            )
        )
    try:
        client_ec2.create_vpc(
            CidrBlock="192.168.0.0/16",
            DryRun=True,
        )
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
                indent=4
            )
        )
    try:
        all_vpcs = client_ec2.describe_vpcs()
        vpc_list = []
        for vpc_id in all_vpcs["Vpcs"]:
            vpc_list.append(vpc_id["VpcId"])
        for vpc_create_sg in vpc_list:
            client_ec2.create_security_group(
                Description="SG",
                GroupName="SGGroup",
                VpcId=vpc_create_sg,
                DryRun=True,
            )
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
                indent=4
            )
        )
    cfnresponse.send(event, context, cfnresponse.SUCCESS, {"Response": "Success"})
    return
