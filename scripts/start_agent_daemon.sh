#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

echo "swarmrepo-agent-runtime 0.1.0 is a helper-only public release."
echo "The full agent daemon entrypoint is intentionally deferred."
echo "Use scripts/start_custom_agent.sh for the reviewed public starter, and"
echo "wait for a later reviewed release before expecting a public daemon here."
