---
name: ios-code-coverage-setup
description: Set up or repair iOS code coverage reporting in CI. Use when a Swift/Xcode project needs PR coverage comments, xcov/scan coverage artifacts, Codemagic PR-required coverage checks, a README coverage badge, GitHub Pages badge hosting, shared Fastlane coverage lanes, or fixes for protected-branch badge publishing failures.
---

# iOS Code Coverage Setup

## Workflow

1. Inspect the existing CI path before editing:
   - `codemagic.yaml`, `.github/workflows/*`, or other CI config.
   - `fastlane/Fastfile`, `Gemfile`, `Package.resolved`, and test scheme settings.
   - README badge URLs and any existing `coverage-badge` branch or GitHub Pages setup.

2. Prefer shared lanes when the project already uses or should use common iOS CI lanes. In Fastlane, import the shared lane repo and call shared coverage lanes from CI rather than copying large lane bodies into app repos.

3. Keep coverage generation in the required test workflow unless the user explicitly wants a separate job. For Codemagic, the robust pattern is:
   - Required PR workflow runs unit tests with code coverage enabled.
   - The same workflow generates the coverage report and PR comment.
   - The same workflow also runs on pushes to the default integration branch.
   - Badge publishing is skipped on PR branches and only writes badge artifacts from the integration branch.

4. Do not make CI push README commits directly to a protected branch. Use a checked-in README badge URL that points to a badge artifact, then let CI update only the badge artifact branch/path.

5. For private GitHub repos, do not use private `raw.githubusercontent.com` badge URLs in README. GitHub README image fetchers often cannot authenticate. Prefer GitHub Pages from a badge branch, or another public static badge host.

6. Validate locally before pushing:
   - Parse YAML with alias support.
   - Check embedded shell scripts with `bash -n`.
   - Run `git diff --check`.
   - Verify the badge URL returns `HTTP 200`.
   - Run the repo-required review skill before committing if repo instructions require it.

## Implementation Reference

Read [codemagic-fastlane-pattern.md](references/codemagic-fastlane-pattern.md) when implementing or debugging the concrete Codemagic/Fastlane/GitHub Pages setup.

## Review Checks

Before declaring done, verify:

- PR builds cannot overwrite shared badge artifacts.
- Default-branch push builds do not require PR-only env vars such as `CM_PULL_REQUEST_NUMBER`.
- Badge publishing does not try to push README changes to a protected branch.
- The README badge URL is public and renders without authentication.
- The required CI check name remains stable if branch protection depends on it.
