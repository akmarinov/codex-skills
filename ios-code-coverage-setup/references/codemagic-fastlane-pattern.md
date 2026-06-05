# Codemagic + Fastlane Coverage Pattern

Use this pattern for iOS Xcode projects using Fastlane and Codemagic.

## Fastlane

Prefer a shared lane import when available:

```ruby
begin
  import_from_git(
    url: ENV['CI_FASTLANE_REPO'] || 'git@github.com:ORG/ios-ci-lanes.git',
    path: 'fastlane/Fastfile',
    branch: ENV['CI_FASTLANE_BRANCH'] || 'main',
    cache_path: ENV['CI_FASTLANE_CACHE_PATH'] || File.expand_path('../.fastlane-imports/ios-ci-lanes', __dir__)
  )
rescue => e
  message = "Shared CI lanes not available (import_from_git failed): #{e}"
  if ENV['CI'] || ENV['CM_BUILD_ID'] || ENV['CM_BUILD_DIR']
    UI.user_error!(message)
  else
    UI.important(message)
  end
end
```

Expected shared lanes:

- `ci_pr_required`: run tests through `scan`.
- `ci_coverage_report`: consume the generated `.xcresult`, run `xcov`, write artifacts, and upsert a PR coverage comment.
- `ci_publish_coverage_badge`: publish badge JSON/SVG artifacts to a badge branch.

When tests and coverage are separate commands, keep coverage enabled in the test command:

```yaml
log-group "Run unit tests" bundle exec fastlane ci_pr_required project:$IOS_PROJECT scheme:$IOS_SCHEME_TESTS coverage:false test_xcargs:"-enableCodeCoverage YES"
log-group "Generate code coverage report" bundle exec fastlane ci_coverage_report project:$IOS_PROJECT scheme:$IOS_SCHEME_TESTS
```

## Codemagic Required Workflow

Keep coverage inside the required test workflow when coverage is a PR gate or PR comment:

```yaml
tests_required: &tests_required
  name: Run unit tests
  script: |
    log-group "Run unit tests" bundle exec fastlane ci_pr_required project:$IOS_PROJECT scheme:$IOS_SCHEME_TESTS coverage:false test_xcargs:"-enableCodeCoverage YES"
  test_report: scan.xml

coverage_report: &coverage_report
  name: Code coverage report
  script: |
    log-group "Generate code coverage report" bundle exec fastlane ci_coverage_report project:$IOS_PROJECT scheme:$IOS_SCHEME_TESTS

publish_coverage_badge: &publish_coverage_badge
  name: Publish coverage badge
  script: |
    log-group "Publish coverage badge" bundle exec fastlane ci_publish_coverage_badge only_branch:develop update_readme_badge:false badge_path:badges/coverage.json badge_svg_path:badges/coverage.svg

workflows:
  pr_required:
    name: PR Required — Tests
    triggering:
      events:
        - push
        - pull_request
      branch_patterns:
        - pattern: 'develop'
          include: true
          source: true
        - pattern: 'develop'
          include: true
          source: false
        - pattern: 'main'
          include: true
          source: false
    scripts:
      - *tests_required
      - *coverage_report
      - *publish_coverage_badge
```

Adjust branch names for repos that use `main`, `master`, or `development`.

The `only_branch` guard is required. PR builds should generate reports/comments, but only the integration branch should update the shared badge branch.

## PR-Only Steps

If the required workflow also runs on default-branch pushes, guard PR-only commands:

```yaml
swiftlint_changed_files: &swiftlint_changed_files
  name: SwiftLint changed files
  script: |
    if [ -n "${CM_PULL_REQUEST_NUMBER:-}" ]; then
      log-group "SwiftLint changed files" bash -c "bundle exec fastlane ci_lint_changed_files \
        pr_number:\"$CM_PULL_REQUEST_NUMBER\" \
        repo_slug:\"$CM_REPO_SLUG\" \
        github_token:\"$GH_TOKEN\""
    else
      log-group "SwiftLint changed files" bash -c "printf '%s\n' '<?xml version=\"1.0\" encoding=\"UTF-8\"?>' '<testsuites tests=\"0\" failures=\"0\" errors=\"0\" skipped=\"0\"></testsuites>' > swiftlint_changed.xml"
    fi
  test_report: swiftlint_changed.xml
```

## README Badge

For private repos, use a public GitHub Pages badge URL:

```markdown
[![Coverage](https://ORG.github.io/REPO/badges/coverage.svg)](https://codemagic.io/apps/CODEMAGIC_APP_ID)
```

Do not use private raw GitHub URLs. Do not rely on a static Shields badge unless stale coverage is acceptable.

## GitHub Pages Badge Branch

Use a dedicated badge branch such as `coverage-badge`. It should contain:

```text
.nojekyll
badges/coverage.json
badges/coverage.svg
```

Enable Pages from that branch and root path:

```bash
gh api repos/ORG/REPO/pages \
  --method POST \
  -F 'source[branch]=coverage-badge' \
  -F 'source[path]=/'
```

If Pages already exists, update it:

```bash
gh api repos/ORG/REPO/pages \
  --method PUT \
  -F 'source[branch]=coverage-badge' \
  -F 'source[path]=/'
```

Verify:

```bash
gh api repos/ORG/REPO/pages --jq '{status:.status, html_url:.html_url, source:.source, public:.public}'
curl -I -L --max-time 15 'https://ORG.github.io/REPO/badges/coverage.svg'
```

## Coverage Exclusions

If coverage should reflect unit-testable business logic rather than UI rendering or app glue, add a repo-owned exclusions file. Keep it explicit and auditable:

```text
# Coverage in CI is the unit-testable app logic surface.
App/
DesignSystem/
Shared/Helpers/
Shared/Extensions/
Managers/NetworkManager/APIService\.swift$
```

Tune the list per repo. Do not hide untested business logic just to improve the percentage.

## Validation Commands

Use these checks after editing Codemagic YAML:

```bash
ruby -e 'require "yaml"; YAML.load_file("codemagic.yaml", aliases: true); puts "YAML OK"'
ruby -e 'require "yaml"; y=YAML.load_file("codemagic.yaml", aliases: true); File.write("/tmp/coverage_report.sh", y["coverage_report"]["script"]); File.write("/tmp/publish_coverage_badge.sh", y["publish_coverage_badge"]["script"]);' && bash -n /tmp/coverage_report.sh && bash -n /tmp/publish_coverage_badge.sh
git diff --check
```

When a failed build is involved, inspect the exact failed step logs before editing. For Codemagic links, use the Codemagic watcher/CLI if available.
