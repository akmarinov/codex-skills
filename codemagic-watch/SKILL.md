---
name: codemagic-watch
description: Inspect and monitor Codemagic builds with the `codemagic-watch` CLI. Use when asked to fetch a build snapshot, watch a Codemagic build until completion, stream Codemagic JSON events into another tool, or react to build success/failure from a Codemagic build ID or build URL.
---

# Codemagic Watch

## Overview

Use this skill to run the `codemagic-watch` CLI from an available checkout or global install and turn Codemagic build state into something actionable for a user or automation. Prefer it when the input is a specific build URL or build ID and the job is to inspect, follow, or react to that build.

## Quick Start

1. Work from the `codemagic-watch` repository root when using a local checkout.
2. Ensure the repository and CLI are available:
   - Canonical repo URL: `https://github.com/akmarinov/codemagic-watch.git`.
   - If a `codemagic-watch` checkout is not present locally, clone it first.
   - If dependencies are missing in a local checkout, run `npm install`.
   - Run `npm run build` inside the `codemagic-watch` checkout before invoking `node dist/cli.js ...`.
   - If the user wants a global install instead of a local checkout, install with `npm install -g git+https://github.com/akmarinov/codemagic-watch.git`.
3. Ensure auth is configured:
   - Prefer `CODEMAGIC_TOKEN`.
   - Use `CODEMAGIC_BASE_URL` only when targeting a non-default Codemagic API host.
4. Prefer `node dist/cli.js ...` inside a checked-out `codemagic-watch` repo. If the package is already installed globally, `codemagic-watch ...` is equivalent.

## Workflow

### 1. Choose the right command

- Use `get <build-id-or-url>` for a one-time snapshot.
- Use `watch <build-id-or-url>` to poll until the build reaches a terminal state.
- Accept either a raw build ID or a full Codemagic build URL. The CLI extracts the build ID from the URL.

### 2. Choose the output shape

- Use default text output for quick human inspection.
- Use `--json` for piping into other tools or for precise event handling.
- Add `--pretty` only when the JSON is primarily for reading, not piping.
- Add `--raw` when the normalized snapshot may omit fields needed for debugging or forward compatibility.

### 3. Tune watch behavior

- Default poll interval is 10 seconds. Lower it only when faster feedback is worth the extra API traffic.
- Use `--timeout <seconds>` to cap waiting time. `0` disables the timeout.
- Use `--max-errors <count>` to tolerate transient Codemagic API failures before giving up.
- Use `--quiet` only with non-JSON watch output when unchanged snapshots would be noisy.

### 4. Interpret the result

- Treat exit code `0` as success.
- Treat exit code `2` as build failure.
- Treat exit code `3` as canceled build.
- Treat exit code `4` as timeout.
- Treat exit code `1` as unknown or unrecoverable failure.
- In JSON mode, pay attention to `complete`, `retry`, and `timeout` events rather than screen text.

## Guardrails

- Stop and fix authentication first if `CODEMAGIC_TOKEN` is missing.
- If the binary is missing, install it from `https://github.com/akmarinov/codemagic-watch.git` rather than assuming an npm-published package exists.
- Do not promise "latest workflow build" support. This CLI watches a specific build only.
- If the build status looks ambiguous, re-run with `--json --raw` and inspect the normalized snapshot plus raw payload.
- For automations, rely on exit codes and the JSON `conclusion` field rather than matching colored terminal output.

## Resources

- `references/usage.md`: Copy-paste command patterns, event examples, and troubleshooting notes.
