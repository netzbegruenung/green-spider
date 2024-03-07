#!/bin/bash

# Creates a server, installs Docker, clones green-directory, creates jobs, runs spider jops, tears down the server.
#
# This will take several hours. For a complete, clean run it is required to leave the
# terminal running the script open. Otherwise the server won't be deleted properly
# which will result in extra cost.
#
# When stopping the script at any point (Ctrl+C), please make sure that the server
# gets deleted afterwards.
#
# Requirements:
#
# - curl
# - jq (https://jqlang.github.io/jq/)
# - ssh
# - SSH key referenced in the server details ("ssh_keys")
# - Credentials:
#   - Hetzner API token in secrets/hetzner-api-token.sh
#   - Service account with write permission for Storage and Datastore in secrets/datastore-writer.json
#   - Git token for read access to https://git.verdigado.com/NB-Public/green-directory.git in secrets/git-clone-token.sh

DOCKERIMAGE="ghcr.io/netzbegruenung/green-spider:latest"

RESULTS_ENTITY_KIND="spider-results"

API_TOKEN_SECRET="secrets/hetzner-api-token.sh"
test -f $API_TOKEN_SECRET || { echo >&2 "File $API_TOKEN_SECRET does not exist."; exit 1; }
source $API_TOKEN_SECRET

GIT_TOKEN_SECRET="secrets/git-clone-token.sh"
test -f $GIT_TOKEN_SECRET || { echo >&2 "File $GIT_TOKEN_SECRET does not exist."; exit 1; }
source $GIT_TOKEN_SECRET

SERVERNAME="spider-$(date | md5 | cut -c1-3)"

# possible values: cx11 (1 core 2 GB), cx21 (2 cores, 4 GB), cx31 (2 cores, 8 GB)
SERVERTYPE="cx21"

function create_server()
{
  echo "Creating server $SERVERNAME"

  # ssh_keys ['Marian'] adds Marian's public key to the server and can be extended.
  # user_data: Ensures that we can detect when the cloud-init setup is done.
  #
  # For the rest: https://docs.hetzner.cloud/#servers-create-a-server
  #
  CREATE_RESPONSE=$(curl -s -X POST https://api.hetzner.cloud/v1/servers \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_TOKEN" \
    -d "{
      \"name\": \"$SERVERNAME\",
      \"server_type\": \"$SERVERTYPE\",
      \"location\": \"fsn1\",
      \"start_after_create\": true,
      \"image\": \"debian-11\",
      \"ssh_keys\": [
        \"Marian\"
      ],
      \"user_data\": \"#cloud-config\nruncmd:\n  - touch /cloud-init-done\n\"
    }")

  # Get ID:
  SERVER_ID=$(echo $CREATE_RESPONSE | jq -r .server.id)

  # Get IP:
  SERVER_IP=$(echo $CREATE_RESPONSE | jq -r .server.public_net.ipv4.ip)

  if [ "$SERVER_ID" = "null" ]; then
    echo "No server created."
    echo $CREATE_RESPONSE | jq .
    exit 1
  fi

  echo "Created server $SERVERNAME with ID $SERVER_ID and IP $SERVER_IP"
}


function wait_for_server()
{
  echo -n "Waiting for the server to be reachable via SSH "

  sleep 30

  STATUS="255"
  while [ "$STATUS" != "0" ]; do
    echo -n "."
    sleep 5
    ssh -o StrictHostKeyChecking=no -q root@$SERVER_IP ls /cloud-init-done &> /dev/null
    STATUS=$?
  done

  echo ""
}


create_server $1
wait_for_server

echo ""
echo "Executing remote commands..."

SSHCMD="ssh -o StrictHostKeyChecking=no -q root@$SERVER_IP"
SCPCMD="scp -o StrictHostKeyChecking=no -q"

$SSHCMD << EOF
  export DEBIAN_FRONTEND=noninteractive

  echo ""
  echo "Update package sources"
  apt-get update -q

  echo ""
  echo "Install dependencies"
  apt-get install -y apt-transport-https git gnupg2 software-properties-common

  echo ""
  echo "Add Docker key"
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc && chmod a+r /etc/apt/keyrings/docker.asc

  # Add the repository to Apt sources
  echo ""
  #echo "Get distro name"
  #. /etc/os-release && echo "$VERSION_CODENAME"

  echo \
    "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
    bullseye stable" | \
    tee /etc/apt/sources.list.d/docker.list > /dev/null

  echo ""
  echo "Resulting /etc/apt/sources.list.d/docker.list"
  cat /etc/apt/sources.list.d/docker.list

  echo ""
  echo "Install Docker packages"
  apt-get update
  apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

  echo ""
  echo "Test docker"
  docker pull hello-world
  docker run --rm hello-world

  mkdir /root/secrets
EOF

echo ""
echo "Copying files to server"
$SCPCMD secrets/datastore-writer.json root@$SERVER_IP:/root/secrets/datastore-writer.json
$SCPCMD docker-compose.yaml root@$SERVER_IP:/root/docker-compose.yaml
$SCPCMD job.py root@$SERVER_IP:/root/job.py
$SCPCMD requirements.txt root@$SERVER_IP:/root/requirements.txt

echo ""
echo "Installing Python dependencies"
$SSHCMD DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pip build-essential
$SSHCMD pip3 install -r requirements.txt

echo ""
echo "Cloning green-directory"
$SSHCMD git clone --progress --depth 1 https://$GIT_TOKEN@git.verdigado.com/NB-Public/green-directory.git /root/cache/green-directory

echo ""
echo "Pulling container images"
$SSHCMD docker compose pull --quiet redis manager

echo ""
echo "Starting redis in background"
$SSHCMD docker compose up --detach redis
sleep 5

echo ""
echo "Creating jobs"
$SSHCMD docker compose up manager

echo ""
echo "Queue status"
$SSHCMD rq info --url redis://localhost:6379

echo ""
echo "Starting worker for first run"
$SSHCMD rq worker --burst high default low --url redis://localhost:6379

echo ""
echo "Re-queuing failed jobs"
$SSHCMD rq requeue --queue low --all --url redis://localhost:6379

echo ""
echo "Queue status:"
$SSHCMD rq info --url redis://localhost:6379

echo ""
echo "Starting worker for second run"
$SSHCMD JOB_TIMEOUT=100 rq worker --burst high default low --url redis://localhost:6379

echo ""
echo "Done."
  


# Delete the box
echo ""
echo "Deleting server $SERVERNAME with ID $SERVER_ID"
curl -s -X DELETE -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_TOKEN" \
  https://api.hetzner.cloud/v1/servers/$SERVER_ID
