#!/bin/bash
#
# Generate SRI hash of file at url: $1

echo -n "sha256-"
curl -s "$1" | openssl dgst -sha256 -binary | openssl base64 -A
echo
