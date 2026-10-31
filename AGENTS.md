# Agent rules

This repo holds the docs for the Mac mini M4 (J773g) Omarchy port. Before you change anything here or in the port repos, read [gravity/AGENT-RULES.md](gravity/AGENT-RULES.md).

The short version:
- Work only in the `techmore` forks. Nothing goes upstream until it passes [the release gate](gravity/RELEASE-GATE-2026-10-31.md) on the owner's M4 mini and the owner approves it.
- CI runs on the M4 mini's self-hosted runners, routed by repo variables, Ubuntu 26.04 only. Batch your pushes.
- On macOS: never `git add -A` in a kernel checkout, always write `${var}` in zsh, and never commit keys.
