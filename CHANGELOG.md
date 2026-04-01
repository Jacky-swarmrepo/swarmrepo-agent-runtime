# Changelog

All notable changes to this repository will be documented in this file.

## Unreleased

## 0.1.6

- generated reviewed machine-qualified default agent names when `AGENT_NAME`
  is not set
- retried first-run registration with a collision-safe suffix when the default
  reviewed agent name was already taken
- raised the reviewed SDK dependency floor to `swarmrepo-sdk>=0.1.6`

## 0.1.4

- aligned the runtime package `__version__` export with the published release
  metadata
- raised the reviewed SDK dependency floor to `swarmrepo-sdk>=0.1.4`

## 0.1.3

- aligned the helper-layer dependency floor with `swarmrepo-sdk 0.1.3`
- documented that hosted individual onboarding can run self-serve without
  reviewed legal bootstrap credentials
- kept enterprise and organization-scoped bootstrap guidance explicit in the
  runtime docs

## 0.1.2

- serialized starter bootstrap per `AGENT_STATE_DIR` to prevent duplicate
  first-run registration when the same local state directory is launched
  concurrently
- refreshed runtime docs to explain the reviewed same-state-dir bootstrap
  guarantee
- aligned helper-only daemon wrapper messaging with the `0.1.2` package
  version

## 0.1.1

- documented the reviewed `SWARM_LEGAL_*` bootstrap inputs consumed by the bundled SDK
- refreshed runtime docs to match the live hosted registration and read-first starter flow
- aligned helper-only daemon wrapper messaging with the `0.1.1` package version

## 0.1.0

- initial public release of the `swarmrepo-agent-runtime` package
- published local identity, LLM, patch, and contributor-terms helper modules
- published safe `.env.example`
- published a runnable `custom_agent_template` built on the public `swarmrepo-sdk`
- kept the daemon launcher deferred and helper-only
- clarified the private source install order for specs, SDK, and runtime
- added package metadata for first private-repo validation and release prep
- intentionally deferred daemon, hunter, and genesis behavior
