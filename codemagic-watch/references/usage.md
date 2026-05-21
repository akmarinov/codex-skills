# Codemagic Watch Usage

## Install sources

- Canonical repository: `https://github.com/akmarinov/codemagic-watch.git`
- Global install from GitHub:

```bash
npm install -g git+https://github.com/akmarinov/codemagic-watch.git
```

- Local checkout setup:

```bash
git clone https://github.com/akmarinov/codemagic-watch.git
cd codemagic-watch
npm install
npm run build
```

## Common commands

Run from the `codemagic-watch` checkout root after `npm run build`:

```bash
node dist/cli.js get <build-id-or-url>
node dist/cli.js get <build-id-or-url> --json --pretty
node dist/cli.js watch <build-id-or-url>
node dist/cli.js watch <build-id-or-url> --interval 5 --timeout 1800
node dist/cli.js watch <build-id-or-url> --json --raw
```

If the package is installed globally, replace `node dist/cli.js` with `codemagic-watch`.

## When to use `get` vs `watch`

- Use `get` when the user wants current metadata for one build.
- Use `watch` when the user wants to wait for completion, stream changes, or trigger follow-up actions from a final state.

## Useful flags

- `--json`: Emit machine-readable output.
- `--pretty`: Pretty-print JSON.
- `--raw`: Include the original Codemagic payload in JSON output.
- `--quiet`: Suppress unchanged snapshot lines in non-JSON watch mode.
- `--interval <seconds>`: Poll cadence for `watch`.
- `--timeout <seconds>`: Stop waiting after a fixed time.
- `--max-errors <count>`: Allow transient failures before exiting.
- `--token <token>`: Override `CODEMAGIC_TOKEN`.
- `--base-url <url>`: Override `CODEMAGIC_BASE_URL`.

## Event shapes to expect in `watch --json`

- `snapshot`: Current normalized build state, with `changed: true|false`.
- `complete`: Terminal result with `conclusion` set to `success`, `failed`, `canceled`, or `unknown`.
- `retry`: Transient API failure with attempt count and error message.
- `timeout`: Watcher timed out before a terminal build state.

## Automation pattern

Use JSON mode when another tool needs structured output:

```bash
node dist/cli.js watch <build-id-or-url> --json
```

Use process exit codes when a shell script only needs pass/fail behavior:

- `0`: success
- `2`: failed
- `3`: canceled
- `4`: timeout
- `1`: unknown or unrecoverable error

## Troubleshooting

- Missing token: export `CODEMAGIC_TOKEN` or pass `--token`.
- Slow or noisy output: increase `--interval` or add `--quiet`.
- Need exact API fields: add `--raw`.
- Repeated transient failures: increase `--max-errors` only if the Codemagic API is flaky and the user wants the watcher to keep trying.
