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


DOCKERIMAGE="quay.io/netzbegruenung/green-spider-webapp:latest"

API_TOKEN_SECRET="secrets/hetzner-api-token.sh"
test -f $API_TOKEN_SECRET || { echo >&2 "File $API_TOKEN_SECRET does not exist."; exit 1; }
source $API_TOKEN_SECRET

# possible values: cx11 (1 core 2 GB), cx21 (2 cores, 4 GB), cx31 (2 cores, 8 GB)
SERVERTYPE="cx11"

# Gets the IP address with description "webapp"
function get_ip()
{
  echo "Getting IP address"

  RESPONSE=$(curl -s https://api.hetzner.cloud/v1/floating_ips \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_TOKEN")

  IP_ID=$(echo $RESPONSE | jq '.floating_ips[] | select(.description == "webapp") | .id')
  IP_IP=$(echo $RESPONSE | jq '.floating_ips[] | select(.description == "webapp") | .ip')
}

function find_webapp_server()
{
  RESPONSE=$(curl -s "https://api.hetzner.cloud/v1/servers?label_selector=purpose=webapp" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_TOKEN")

  CURRENT_SERVER_ID=$(echo $RESPONSE | jq '.servers[0] | .id')
  
  if [ "$CURRENT_SERVER_ID" = "null" ]; then
    echo "Currently there is no server"
  else
    echo "Current server has ID $CURRENT_SERVER_ID"
  fi
  
}

function create_server()
{
  SERVERNAME=webapp-$(date -u '+%FT%H-%M')
  echo "Creating server named $SERVERNAME"

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
      \"labels\": {\"purpose\": \"webapp\"},
      \"user_data\": \"#cloud-config\nruncmd:\n  - touch /cloud-init-done\n\"
    }")

  # Get ID:
  SERVER_ID=$(echo $CREATE_RESPONSE | jq -r .server.id)

  # Get IP:
  SERVER_IP=$(echo $CREATE_RESPONSE | jq -r .server.public_net.ipv4.ip)

  echo "Created server with ID $SERVER_ID and IP $SERVER_IP"
}

function assign_ip()
{
  curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer $API_TOKEN" \
    https://api.hetzner.cloud/v1/floating_ips/${IP_ID}/actions/assign \
    -d "{\"server\": ${SERVER_ID}}"
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

get_ip
echo "webapp IP address has ID ${IP_ID}"

find_webapp_server

create_server
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
EOF

echo "Done with remote setup."

echo "Launching server"

ssh -o StrictHostKeyChecking=no root@$SERVER_IP \
    docker pull $DOCKERIMAGE

ssh -o StrictHostKeyChecking=no root@$SERVER_IP \
    docker run --name webapp -d \
      -p 443:443 -p 80:8000 \
      -v /letsencrypt/etc:/etc/letsencrypt \
      $DOCKERIMAGE

# Assign the IP to the new server
assign_ip
ssh -o StrictHostKeyChecking=no root@$SERVER_IP sudo ip addr add $IP_IP dev eth0

# remove old server
if [ "$CURRENT_SERVER_ID" != "null" ]; then
  echo "Deleting old webapp server with ID $CURRENT_SERVER_ID"
  curl -s -X DELETE -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_TOKEN" \
    https://api.hetzner.cloud/v1/servers/$CURRENT_SERVER_ID
fi
