#!/bin/bash
echo "------ configuring cloudshell environment -------"
wget https://bootstrap.pypa.io/get-pip.py
python3 ./get-pip.py
pip3 install git-remote-codecommit --user --quiet
git clone codecommit://workshop_repo
cd workshop_repo/
npm i
python3 -m venv .venv
. .venv/bin/activate
.venv/bin/pip3 install -r requirements.txt --quiet
sudo wget -qO /usr/bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64
sudo chmod +x /usr/bin/yq
git config --global user.email "participant@example.com"
git config --global user.name "Participant SEC203"
echo "------ cloudshell environment configured -------"
python3 --version
yq --version
npx cdk --version
echo ${VIRTUAL_ENV}
echo "------------------------------------------------"