# ADR 0002: GitHub is the canonical code remote

- Status: accepted
- Date: 2026-08-18

## Decision

Developer machines and the home server use independent Git clones. Changes move through commits
and branches on GitHub. Server synchronization performs only a fast-forward update of a clean
checkout over key-authenticated SSH.

## Consequences

There is one understandable history and no ambiguous bidirectional filesystem synchronization.
Runtime data requires a separate storage and backup design.
