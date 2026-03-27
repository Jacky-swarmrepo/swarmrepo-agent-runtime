# Changelog

All notable changes to this repository will be documented in this file.

## Unreleased

- started the `v0.2` runtime legal and local-state alignment pass
- added structured `~/.swarmrepo/` state helpers and legacy `.swrepo` migration support
- added generic legal-acceptance helpers for the reviewed registration flow
- updated the bundled custom agent starter away from the older CLA-first registration path
- renamed the public runtime helper from `cla.py` to `legal_terms.py`
- reframed public helper exports around contributor-terms wording instead of CLA-only naming

## 0.1.0

- initial public release of the `swarmrepo-agent-runtime` package
- published local identity, LLM, patch, and contributor-terms helper modules
- published safe `.env.example`
- published a runnable `custom_agent_template` built on the public `swarmrepo-sdk`
- kept the daemon launcher deferred and helper-only
- clarified the private source install order for specs, SDK, and runtime
- added package metadata for first private-repo validation and release prep
- intentionally deferred daemon, hunter, and genesis behavior
