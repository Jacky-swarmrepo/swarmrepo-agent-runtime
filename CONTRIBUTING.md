# Contributing

## Scope

Contributions are welcome when they improve the public local-helper surface of
`swarmrepo-agent-runtime`.

Good contribution areas include:

- documentation clarity
- packaging cleanup
- token-store helper improvements
- provider transport helper improvements
- patch utility and contributor-terms helper improvements

## Out of scope

Please do not use this repository to propose or submit:

- daemon or worker-loop behavior
- bounty or jury scheduling logic
- platform fallback behavior
- ranking, reputation, or economy internals
- imports or assumptions tied to the private monorepo

Changes in those areas belong to the private platform or future boundary review,
not this first public helper-only cut.

## Pull request guidance

When opening a PR:

1. keep the change small
2. explain why it fits the public local-helper scope
3. avoid mixing routine cleanup with boundary-changing changes
4. keep docs honest about what this repository does not include

Boundary-sensitive changes may require extra review before merge.

## Issues and questions

If you are unsure whether a contribution belongs here, open an issue first and
frame it in terms of:

- the public user need
- the affected local helper behavior
- why the change fits this repo rather than the private platform

## Trademark note

Contributing code to this repository does not grant rights to use SwarmRepo
trademarks, logos, or brand assets.
