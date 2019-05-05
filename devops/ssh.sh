#!/bin/bash

# Log in to webapp server via SSH

API_TOKEN_SECRET="secrets/hetzner-api-token.sh"
test -f $API_TOKEN_SECRET || { echo >&2 "File $API_TOKEN_SECRET does not exist."; exit 1; }
source $API_TOKEN_SECRET

source devops/functions.bash

get_ip

echo "Use this command for SSH access:"
echo "ssh -o StrictHostKeyChecking=no root@${IP_IP}"

ssh -o StrictHostKeyChecking=no root@${IP_IP}
