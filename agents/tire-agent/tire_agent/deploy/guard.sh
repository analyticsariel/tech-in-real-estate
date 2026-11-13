#!/usr/bin/env bash
# Sourced by every tire-agent deploy script. Refuses to run unless the active credentials belong to
# the TiRE account. This machine's default AWS profile is a different account that must never be touched.
set -euo pipefail
TIRE_ACCOUNT="${TIRE_AWS_ACCOUNT_ID:?set TIRE_AWS_ACCOUNT_ID to your AWS account id}"
TIRE_REGION=us-east-1
AWS_BIN=${AWS_BIN:-$(command -v aws)}
tire_aws() { "$AWS_BIN" --region "$TIRE_REGION" ${TIRE_PROFILE:+--profile "$TIRE_PROFILE"} "$@"; }
actual=$(tire_aws sts get-caller-identity --query Account --output text)
if [[ "$actual" != "$TIRE_ACCOUNT" ]]; then
  echo "refusing: credentials are for account $actual, not $TIRE_ACCOUNT" >&2
  exit 1
fi
