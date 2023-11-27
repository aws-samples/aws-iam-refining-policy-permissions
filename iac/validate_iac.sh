#!/bin/bash
echo "--------- Generating IaC.yaml --------- "
. .venv/bin/activate
npx cdk synth \
      --asset-metadata false \
      --path-metadata false \
      --version-reporting false > iac.yaml
# automatic removal of references to AWS CDK bootstrap using `yq`
yq -i 'del(.Rules)' iac.yaml
yq -i 'del(.Parameters.BootstrapVersion)' iac.yaml
echo "--------- IaC generated ---------"
cat iac.yaml
echo "---------------------------------"