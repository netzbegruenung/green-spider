# Gets the IP address with description "webapp"
# and stores it in the $IP_IP variable
function get_ip()
{
  echo "Getting IP address"

  RESPONSE=$(curl -s https://api.hetzner.cloud/v1/floating_ips \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $API_TOKEN")

  IP_ID=$(echo $RESPONSE | jq -r '.floating_ips[] | select(.description == "webapp") | select(.type == "ipv4") | .id')
  IP_IP=$(echo $RESPONSE | jq -r '.floating_ips[] | select(.description == "webapp") | select(.type == "ipv4") | .ip')
}

