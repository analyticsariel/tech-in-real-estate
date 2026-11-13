#!/usr/bin/env bash
# One-time: create the OIDC provider, deploy roles, boundary, artifacts bucket, and image repo.
# Run by a human with the account's admin profile. CI never runs this.
#   TIRE_PROFILE=my-aws-profile tire_agent/deploy/bootstrap.sh [budget-email]
set -euo pipefail
: "${TIRE_PROFILE:?set TIRE_PROFILE (e.g. my-aws-profile); the default profile is not allowed}"
here=$(cd "$(dirname "$0")" && pwd)
source "$here/guard.sh"
tire_aws cloudformation deploy \
  --stack-name tire-agent-bootstrap \
  --template-file "$here/bootstrap.yaml" \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides "BudgetEmail=${1:-}" \
  --tags project=tire-agent \
  --no-fail-on-empty-changeset
tire_aws cloudformation describe-stacks --stack-name tire-agent-bootstrap --query 'Stacks[0].Outputs' --output table
