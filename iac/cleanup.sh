#!/bin/bash
region=${1}
buckets=$(aws s3api list-buckets --query "Buckets[].Name" --output text)
for bucket in ${buckets}; do
    if  [[ "${bucket}" =~ workshopcommonstack-allpurposes3bucket.*$ ]]; then
      aws s3 rb --force s3://${bucket}
      echo "${bucket} deleted"
    fi
    if [[ "${bucket}" =~ workshoppipelinestack-iacscanpipelineartifactsbucket.*$ ]]; then
      aws s3 rb --force s3://${bucket}
      echo "${bucket} deleted"
    fi
done
loggroups=$(aws logs describe-log-groups --query "logGroups[].logGroupName" --output text --region ${region})
for loggroup in ${loggroups}; do
    echo ${loggroup}
    if  [[ "${loggroup}" =~ ^/aws/lambda/WorkshopUnusedAccess.*$ ]]; then
      aws logs delete-log-group --log-group-name ${loggroup} --region ${region}
      echo "${loggroup} deleted"
    fi
    if  [[ "${loggroup}" =~ ^/aws/lambda/WorkshopPolicyValidator.*$ ]]; then
      aws logs delete-log-group --log-group-name ${loggroup} --region ${region}
      echo "${loggroup} deleted"
    fi
    if  [[ "${loggroup}" =~ ^/aws/lambda/WorkshopLastAccessed.*$ ]]; then
      aws logs delete-log-group --log-group-name ${loggroup} --region ${region}
      echo "${loggroup} deleted"
    fi
    if  [[ "${loggroup}" =~ ^/aws/lambda/WorkshopCustomPolicyCheck.*$ ]]; then
      aws logs delete-log-group --log-group-name ${loggroup} --region ${region}
      echo "${loggroup} deleted"
    fi
    if  [[ "${loggroup}" =~ ^/aws/lambda/WorkshopAnalyzerStack.*$ ]]; then
      aws logs delete-log-group --log-group-name ${loggroup} --region ${region}
      echo "${loggroup} deleted"
    fi
    if  [[ "${loggroup}" =~ ^/aws/lambda/IacScan.*$ ]]; then
      aws logs delete-log-group --log-group-name ${loggroup} --region ${region}
      echo "${loggroup} deleted"
    fi
    if  [[ "${loggroup}" =~ ^/aws/lambda/WorkshopCommonStack.*$ ]]; then
      aws logs delete-log-group --log-group-name ${loggroup} --region ${region}
      echo "${loggroup} deleted"
    fi
    if  [[ "${loggroup}" =~ ^/aws/lambda/WorkshopPipelineStack.*$ ]]; then
      aws logs delete-log-group --log-group-name ${loggroup} --region ${region}
      echo "${loggroup} deleted"
    fi
done