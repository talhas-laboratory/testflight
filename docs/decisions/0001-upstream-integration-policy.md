# ADR 0001: Integrate upstreams through owned adapters

- Status: accepted
- Date: 2026-08-18

## Decision

Consume upstream releases as optional packages or containers and isolate them behind adapters.
Track exact releases and commits in `upstreams/registry.yaml`. Require a new ADR before using a
submodule, maintaining a fork, or copying upstream source.

## Consequences

The initial integration takes slightly more structure, but upgrades, replacements, licensing,
and independent testing remain tractable as the number of upstream projects grows.
