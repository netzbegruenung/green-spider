#!/bin/bash

# Creates a server, installs Docker, runs the screenshots job, tears down the server.
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
# - jq (https://stedolan.github.io/jq/)
# - ssh
# - SSH key referenced in the server details ("ssh_keys")
# - Service account with write permission for Storage and Datastore in 
#   secrets/datastore-writer.json


DOCKERIMAGE="quay.io/netzbegruenung/green-spider:latest"

RESULTS_ENTITY_KIND="spider-results"

API_TOKEN_SECRET="secrets/hetzner-api-token.sh"
test -f $API_TOKEN_SECRET || { echo >&2 "File $API_TOKEN_SECRET does not exist."; exit 1; }
source $API_TOKEN_SECRET


if [[ "$1" = "" ]]; then
  echo "No argument given. Please use 'screenshotter' or 'spider' as arguments."
  exit 1
fi

SERVERNAME="$1-$(date | md5 | cut -c1-3)"

# possible values: cx11 (1 core 2 GB), cx21 (2 cores, 4 GB), cx31 (2 cores, 8 GB)
SERVERTYPE="cx21"

function create_server()
{
  echo "Creating server $SERVERNAME"

  # server_type 'cx11' is the smallest, cheapest category.
  # location 'nbg1' is Nürnberg/Nuremberg, Germany.
  # image 'debian-9' is a plain Debian stretch.
  # ssh_keys ['Marian'] adds Marian's public key to the server and can be extended.
  # user_data: Ensures that we can detect when the cloud-init setup is done.
  #
  CREATE_RESPONSE=$(curl -s -X POST https://api.hetzner.cloud/v1/servers \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_TOKEN" \
    -d "{
      \"name\": \"$SERVERNAME\",
      \"server_type\": \"$SERVERTYPE\",
      \"location\": \"nbg1\",
      \"start_after_create\": true,
      \"image\": \"debian-9\",
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

echo "Executing remote commands..."

ssh -o StrictHostKeyChecking=no -q root@$SERVER_IP << EOF
  DEBIAN_FRONTEND=noninteractive
  
  echo ""
  echo "Update package sources"
  apt-get update -q

  echo ""
  echo "Install dependencies"
  apt-get install -y curl apt-transport-https gnupg2 software-properties-common

  echo ""
  echo "Add docker repo key"
  curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add -

  echo ""
  echo "Add repo"
  add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian stretch stable"

  echo ""
  echo "Update package sources again"
  apt-get update -q

  echo ""
  echo "Install docker"
  apt-get install -y docker-ce

  mkdir /root/secrets
EOF

echo "Done with remote setup."

if [[ $1 == "screenshotter" ]]; then
  ### screenshotter

  # Copy service account secret to server
  echo "Copying secret to /root/secrets/service-account.json"
  scp -o StrictHostKeyChecking=no -q secrets/datastore-writer.json root@$SERVER_IP:/root/secrets/service-account.json

  # Run docker job
  echo "Starting Docker Job"
  ssh -o StrictHostKeyChecking=no -q root@$SERVER_IP docker run -t \
    -v /root/secrets:/secrets \
    quay.io/netzbegruenung/green-spider-screenshotter

else
  ### spider

  # Copy service account secret to server
  echo "Copying secret to /root/secrets/datastore-writer.json"
  scp -o StrictHostKeyChecking=no -q secrets/datastore-writer.json root@$SERVER_IP:/root/secrets/datastore-writer.json

  # Run docker job
  echo "Starting Docker Job"
  #ssh -o StrictHostKeyChecking=no -q root@$SERVER_IP docker run -t \
  #  -v /root/secrets:/secrets \
  #  quay.io/netzbegruenung/green-spider spider.py \
  #  --credentials-path /secrets/datastore-writer.json \
  #  jobs

  ssh -o StrictHostKeyChecking=no -q root@$SERVER_IP mkdir -p /dev-shm
  ssh -o StrictHostKeyChecking=no -q root@$SERVER_IP docker run -t \
    -v /dev-shm:/dev/shm \
    -v /root/secrets:/secrets \
    $DOCKERIMAGE \
    --credentials-path /secrets/datastore-writer.json \
    --loglevel info \
    spider --kind $RESULTS_ENTITY_KIND

fi

# Delete the box
echo "Deleting server $SERVERNAME with ID $SERVER_ID"
curl -s -X DELETE -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_TOKEN" \
  https://api.hetzner.cloud/v1/servers/$SERVER_ID
