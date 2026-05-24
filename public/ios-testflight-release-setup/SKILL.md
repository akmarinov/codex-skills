---
name: ios-testflight-release-setup
description: End-to-end setup for a new iOS app repo that must be created, signed, wired to App Store Connect/TestFlight, and deployed by GitHub Actions. Use when creating or hardening an iOS app release pipeline with XcodeGen/Xcode, fastlane match, GitHub repos/secrets/environments, App Store Connect API keys, hosted or self-hosted macOS runners, and first TestFlight upload verification.
---

# iOS TestFlight Release Setup

Use this skill when the user wants a new iOS app repo shipped to TestFlight, not just scaffolded. Treat repo creation, bundle/App Store Connect setup, signing, GitHub Actions, environment secrets, and first upload as one deliverable.

## Operating Principles

- Prefer a hosted GitHub runner with `macos-26` and `fastlane match` for durable CI signing.
- Use self-hosted macOS runners when private-repo GitHub Actions minutes are exhausted or when local Apple tooling is required. Every job that must avoid minutes needs `runs-on: [self-hosted, macOS]` or a more specific self-hosted label; one leftover `macos-*` job still consumes/bills minutes.
- Use a self-hosted local-keychain runner only as a fallback when match cannot be seeded yet.
- If working in the user's AM Software apps, inspect an already-working app first, especially `VideoMerger`, and mirror its signing/CI shape where applicable.
- Do not declare success from a local upload alone. Verify the remote GitHub Actions run and App Store Connect build state.
- Keep destructive signing actions explicit. Do not revoke, nuke, or delete certificates/profiles without clear approval.

## Required Tools

Check early:

```bash
command -v gh asc xcodegen fastlane jq security git xcodebuild
```

Use local authenticated sessions when available:

```bash
gh auth status
asc auth status
asc apps list --bundle-id "$BUNDLE_ID" --output json
```

## Workflow

1. **Create and inspect the repo**

   - Create the app repo and push an initial `main`.
   - If a private match repo is needed, create it separately, usually `<app>-certificates`.
   - Add or confirm `.gitignore`, `README.md`, `project.yml`, app source, tests, `fastlane/`, and `.github/workflows/`.

   Example:

   ```bash
   gh repo create OWNER/APP_REPO --private --source . --remote origin --push
   gh repo create OWNER/MATCH_REPO --private
   ```

2. **Create the Xcode app**

   Prefer `project.yml` plus `xcodegen generate` when the repo uses XcodeGen.

   Required release settings:

   - `DEVELOPMENT_TEAM`
   - `PRODUCT_BUNDLE_IDENTIFIER`
   - `MARKETING_VERSION`
   - `CURRENT_PROJECT_VERSION`
   - Release signing configured for App Store when using match:

   ```yaml
   settings:
     base:
       DEVELOPMENT_TEAM: TEAMID
       MARKETING_VERSION: "1.0"
       CURRENT_PROJECT_VERSION: "1"
   targets:
     App:
       settings:
         base:
           PRODUCT_BUNDLE_IDENTIFIER: com.example.app
           CODE_SIGN_STYLE: Automatic
         configs:
           Release:
             CODE_SIGN_STYLE: Manual
             CODE_SIGN_IDENTITY: Apple Distribution
             PROVISIONING_PROFILE_SPECIFIER: match AppStore com.example.app
   ```

   Add export compliance when the app does not use non-exempt encryption:

   ```xml
   <key>ITSAppUsesNonExemptEncryption</key>
   <false/>
   ```

   Validate:

   ```bash
   xcodegen generate
   plutil -lint App/Info.plist
   xcodebuild -project App.xcodeproj -scheme App -configuration Debug -destination 'platform=iOS Simulator,name=iPhone 17 Pro' test
   ```

3. **Create App Store Connect records**

   Resolve/create:

   - Bundle ID
   - App Store Connect app
   - App Store Connect API key
   - App Store signing certificate
   - App Store provisioning profile

   Useful checks:

   ```bash
   asc apps list --bundle-id "$BUNDLE_ID" --output json
   asc bundle-ids list --output json --paginate
   asc certificates list --output json --paginate
   asc profiles list --output json --paginate
   ```

4. **Configure fastlane**

   `fastlane/Matchfile`:

   ```ruby
   git_url("https://github.com/OWNER/MATCH_REPO.git")
   storage_mode("git")
   type("appstore")
   app_identifier(["com.example.app"])
   username("apple-id@example.com")
   ```

   Core `Fastfile` pattern:

   ```ruby
   def ensure_app_store_connect_api_key!
     return if defined?(@app_store_api_key) && @app_store_api_key
     key_id = ENV["APP_STORE_CONNECT_API_KEY_ID"]
     issuer_id = ENV["APP_STORE_CONNECT_ISSUER_ID"]
     key_path = ENV["APP_STORE_CONNECT_API_KEY_PATH"] || "fastlane/AuthKey.p8"
     UI.user_error!("APP_STORE_CONNECT_API_KEY_ID is not set") unless key_id
     UI.user_error!("APP_STORE_CONNECT_ISSUER_ID is not set") unless issuer_id
     UI.user_error!("App Store Connect API key not found at #{key_path}") unless File.exist?(key_path)
     @app_store_api_key = app_store_connect_api_key(
       key_id: key_id,
       issuer_id: issuer_id,
       key_filepath: key_path
     )
     ENV.delete("APP_STORE_CONNECT_API_KEY_PATH")
     ENV.delete("DELIVER_API_KEY_PATH")
   end

   def match_readonly?
     override = ENV["MATCH_READONLY_OVERRIDE"]
     return override.downcase == "true" if override
     !ENV["CI"]
   end

   def match_keychain_options
     keychain = ENV["MATCH_KEYCHAIN_NAME"]
     password = ENV["MATCH_KEYCHAIN_PASSWORD"]
     return {} unless keychain && password
     { keychain_name: keychain, keychain_password: password }
   end

   platform :ios do
     lane :certificates do
       ensure_app_store_connect_api_key!
       match(type: "appstore", readonly: match_readonly?, api_key: @app_store_api_key, **match_keychain_options)
     end

     lane :build_release do
       ensure_app_store_connect_api_key!
       increment_build_number(build_number: ENV["GITHUB_RUN_NUMBER"] || Time.now.utc.strftime("%Y%m%d%H%M%S"))
       match(type: "appstore", readonly: match_readonly?, api_key: @app_store_api_key, **match_keychain_options)
       gym(
         scheme: "App",
         configuration: "Release",
         export_method: "app-store",
         export_options: {
           provisioningProfiles: {
             "com.example.app" => "match AppStore com.example.app"
           }
         }
       )
     end

     lane :deploy_testflight do
       build_release
       pilot(api_key: @app_store_api_key, skip_waiting_for_build_processing: true)
     end

     lane :submit_to_app_store do
       build_release
       ENV.delete("APP_STORE_CONNECT_API_KEY_PATH")
       ENV.delete("DELIVER_API_KEY_PATH")
       upload_to_app_store(
         api_key: @app_store_api_key,
         force: true,
         skip_metadata: true,
         skip_screenshots: true,
         submit_for_review: false,
         automatic_release: false,
         precheck_include_in_app_purchases: false
       )
     end
   end
   ```

   If passing `api_key:` to `pilot`, `deliver`, or `upload_to_app_store`, clear `APP_STORE_CONNECT_API_KEY_PATH` and `DELIVER_API_KEY_PATH` after creating the API key object. Otherwise Fastlane can see both `api_key` and `api_key_path` and fail with conflicting authentication inputs.

   Do not set `reject_if_possible` by default in an App Store upload lane. It can cancel an in-progress App Store review when all the user asked for is uploading a new build.

5. **Seed match**

   Prefer importing an existing known-good `.p12` and App Store provisioning profile into the match repo. Keep the P12 password separate from `MATCH_PASSWORD`.

   Critical checks:

   - `MATCH_PASSWORD` is the encryption password for the match repo.
   - The P12 password is only for importing/exporting the certificate.
   - Do not copy encrypted cert files from one match repo into another unless you know both repos use the same `MATCH_PASSWORD`. GitHub secrets cannot be read back, and a wrong password will fail before signing with `Invalid password passed via 'MATCH_PASSWORD'`.
   - When a distribution certificate limit is reached, set match read-only and import/reuse a valid existing distribution cert/profile, or get explicit approval to revoke/free a slot. Do not let CI repeatedly try to create new distribution certs.
   - In a match repo, certificate files should be named by the Developer Portal certificate id, not a local keychain SHA/fingerprint.
   - If fastlane says `Certificate '<hash>' (stored in your storage) is not available on the Developer Portal`, the match repo probably has wrongly named cert files or stale certs.

   Verify certificate id by serial:

   ```bash
   asc certificates list --output json --paginate |
     jq -r '.data[] | [.id, .attributes.serialNumber, .attributes.certificateType, .attributes.displayName] | @tsv'
   ```

   Verify match repo contents:

   ```bash
   git ls-remote https://github.com/OWNER/MATCH_REPO.git
   ```

6. **Create GitHub Actions environment secrets**

   Use a protected environment such as `production`. Required secrets for hosted match-backed deploys:

   ```text
   MATCH_PASSWORD
   MATCH_GIT_BASIC_AUTHORIZATION
   APP_STORE_CONNECT_API_KEY
   APP_STORE_CONNECT_API_KEY_ID
   APP_STORE_CONNECT_ISSUER_ID
   ```

   Optional/common legacy names, only if the workflow reads them:

   ```text
   APPLE_DEVELOPER_TEAM_ID
   APP_STORE_CONNECT_TEAM_ID
   APP_STORE_CONNECT_KEY_ID
   APP_STORE_CONNECT_KEY_CONTENT
   FASTLANE_USER
   ```

   `MATCH_GIT_BASIC_AUTHORIZATION` must be base64 for `x-access-token:<github_pat>`.

   ```bash
   printf 'x-access-token:%s' "$GITHUB_PAT" | base64 | tr -d '\n'
   ```

   If zsh prints a trailing `%`, do not paste `%`; it is only a no-newline marker.

   Set secrets:

   ```bash
   printf '%s' "$MATCH_PASSWORD" |
     gh secret set MATCH_PASSWORD --repo OWNER/APP_REPO --env production

   printf '%s' "$MATCH_GIT_BASIC_AUTHORIZATION" |
     gh secret set MATCH_GIT_BASIC_AUTHORIZATION --repo OWNER/APP_REPO --env production

   gh secret set APP_STORE_CONNECT_API_KEY --repo OWNER/APP_REPO --env production < AuthKey_XXXX.p8
   printf '%s' "$APP_STORE_CONNECT_API_KEY_ID" |
     gh secret set APP_STORE_CONNECT_API_KEY_ID --repo OWNER/APP_REPO --env production
   printf '%s' "$APP_STORE_CONNECT_ISSUER_ID" |
     gh secret set APP_STORE_CONNECT_ISSUER_ID --repo OWNER/APP_REPO --env production
   ```

7. **Add hosted GitHub Actions deploy workflow**

   Prefer `macos-26`; App Store Connect may reject older SDK uploads.

   ```yaml
   name: App Store Deployment

   on:
     push:
       branches: [ main ]
     workflow_dispatch:

   concurrency:
     group: app-store-deployment-${{ github.ref }}
     cancel-in-progress: false

   env:
     XCODE_PATH: ${{ vars.XCODE_PATH || '/Applications/Xcode_26.4.app/Contents/Developer' }}
     FASTLANE_VERSION: '2.229.1'

   jobs:
     deploy:
       name: Deploy to TestFlight
       runs-on: macos-26
       environment: production
       env:
         RUBY_VERSION: '3.1.4'
         MATCH_PASSWORD: ${{ secrets.MATCH_PASSWORD }}
         MATCH_GIT_BASIC_AUTHORIZATION: ${{ secrets.MATCH_GIT_BASIC_AUTHORIZATION }}
         MATCH_READONLY_OVERRIDE: ${{ vars.MATCH_READONLY_OVERRIDE || 'true' }}
         APP_STORE_CONNECT_API_KEY_PATH: ${{ github.workspace }}/fastlane/AuthKey.p8
         APP_STORE_CONNECT_API_KEY_ID: ${{ secrets.APP_STORE_CONNECT_API_KEY_ID }}
         APP_STORE_CONNECT_ISSUER_ID: ${{ secrets.APP_STORE_CONNECT_ISSUER_ID }}
         SPACESHIP_CONNECT_API_IN_HOUSE: 'false'

       steps:
       - uses: actions/checkout@v4
         with:
           fetch-depth: 0

       - name: Clear checkout GitHub token header
         run: git config --local --unset-all http.https://github.com/.extraheader || true

       - uses: ruby/setup-ruby@v1
         with:
           ruby-version: ${{ env.RUBY_VERSION }}

       - name: Install dependencies
         run: gem install fastlane -v "$FASTLANE_VERSION" --no-document

       - name: Configure Xcode version
         shell: bash
         run: |
           TARGET_PATH="$XCODE_PATH"
           if [ ! -d "$TARGET_PATH" ]; then
             TARGET_PATH="$(xcode-select -p)"
             echo "Requested Xcode path not found; falling back to $TARGET_PATH"
           fi
           echo "DEVELOPER_DIR=$TARGET_PATH" >> "$GITHUB_ENV"

       - name: Setup temporary keychain
         run: |
           set -euo pipefail
           KEYCHAIN_PATH="$RUNNER_TEMP/fastlane_${{ github.run_id }}.keychain-db"
           KEYCHAIN_PASSWORD="$(openssl rand -hex 16)"
           security create-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
           security set-keychain-settings -lut 21600 "$KEYCHAIN_PATH"
           security unlock-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN_PATH"
           security list-keychains -d user -s "$KEYCHAIN_PATH"
           {
             echo "KEYCHAIN_PATH=$KEYCHAIN_PATH"
             echo "KEYCHAIN_PASSWORD=$KEYCHAIN_PASSWORD"
             echo "MATCH_KEYCHAIN_NAME=$KEYCHAIN_PATH"
             echo "MATCH_KEYCHAIN_PASSWORD=$KEYCHAIN_PASSWORD"
           } >> "$GITHUB_ENV"

       - name: Configure App Store Connect API key
         env:
           APP_STORE_CONNECT_API_KEY: ${{ secrets.APP_STORE_CONNECT_API_KEY }}
         run: |
           mkdir -p fastlane
           python3 - <<'PY'
           import json, os, pathlib
           secret = os.environ.get('APP_STORE_CONNECT_API_KEY', '').strip()
           if not secret:
               raise SystemExit('APP_STORE_CONNECT_API_KEY secret is empty')
           key_path = pathlib.Path(os.environ.get('APP_STORE_CONNECT_API_KEY_PATH', 'fastlane/AuthKey.p8'))
           key_id = os.environ.get('APP_STORE_CONNECT_API_KEY_ID')
           issuer_id = os.environ.get('APP_STORE_CONNECT_ISSUER_ID')
           try:
               data = json.loads(secret)
           except json.JSONDecodeError:
               key_material = secret
           else:
               key_material = data.get('key')
               key_id = data.get('key_id', key_id)
               issuer_id = data.get('issuer_id', issuer_id)
           if not key_material:
               raise SystemExit('App Store Connect key material missing from secret')
           if not key_id or not issuer_id:
               raise SystemExit('APP_STORE_CONNECT_API_KEY_ID or APP_STORE_CONNECT_ISSUER_ID missing')
           key_path.write_text(key_material.strip() + ("\n" if not key_material.endswith('\n') else ''))
           key_path.chmod(0o600)
           with open(os.environ['GITHUB_ENV'], 'a') as env:
               env.write(f"APP_STORE_CONNECT_API_KEY_ID={key_id}\n")
               env.write(f"APP_STORE_CONNECT_ISSUER_ID={issuer_id}\n")
           PY

       - name: Release prerequisites preflight
         run: scripts/ci-release-preflight.sh

       - name: Ensure provisioning profile directory writable
         run: |
           PROFILE_DIR="$HOME/Library/MobileDevice/Provisioning Profiles"
           mkdir -p "$PROFILE_DIR"
           chmod u+rwX "$HOME/Library/MobileDevice" "$PROFILE_DIR"
           rm -f "$PROFILE_DIR"/*.mobileprovision || true

       - name: Setup Match certificates
         run: fastlane _${FASTLANE_VERSION}_ certificates

       - name: Deploy to TestFlight
         env:
           GITHUB_RUN_NUMBER: ${{ github.run_number }}
         run: fastlane _${FASTLANE_VERSION}_ deploy_testflight
   ```

8. **Add a preflight script**

   Keep it focused on cheap local checks; do not duplicate fragile App Store network auth checks when fastlane already validates them.

   ```bash
   #!/usr/bin/env bash
   set -euo pipefail

   MATCH_REPO="${MATCH_REPO:-https://github.com/OWNER/MATCH_REPO.git}"

   for var in APP_STORE_CONNECT_API_KEY_ID APP_STORE_CONNECT_ISSUER_ID APP_STORE_CONNECT_API_KEY_PATH MATCH_GIT_BASIC_AUTHORIZATION; do
     if [ -z "${!var:-}" ]; then
       echo "$var is required." >&2
       exit 1
     fi
   done

   [ -f "$APP_STORE_CONNECT_API_KEY_PATH" ] || {
     echo "App Store Connect API key file not found: $APP_STORE_CONNECT_API_KEY_PATH" >&2
     exit 1
   }

   git -c credential.helper= \
     -c http.extraHeader="Authorization: Basic $MATCH_GIT_BASIC_AUTHORIZATION" \
     ls-remote "$MATCH_REPO" >/dev/null

   echo "Release prerequisites are present."
   ```

9. **Self-hosted local-keychain fallback**

   Use this only when match cannot be seeded. The reliable pattern on this Mac was an interactive runner process with login-keychain access. A LaunchAgent/service runner can see certificates but still fail `codesign` with `errSecInternalComponent` because private-key use is blocked non-interactively.

   Fallback checklist:

   - Use a dedicated runner label, e.g. `app-local-keychain`.
   - Start runner interactively from Terminal.
   - Ensure the distribution cert/private key is usable from `login.keychain-db`.
   - Add `security list-keychains -d user -s "$KEYCHAIN" ...` and `security unlock-keychain`.
   - Treat this as temporary until match-backed hosted CI works.

10. **Self-hosted minute-saving runner pattern**

   For private repos with no Actions minutes left, run the complete deploy job on a self-hosted Mac runner. Repo-specific runners are fine; verify the runner is online before chasing workflow bugs:

   ```bash
   gh api repos/OWNER/APP_REPO/actions/runners \
     --jq '.runners[] | {name,status,busy,labels:[.labels[].name]}'
   ```

   Practical workflow hardening for this Mac:

   - Add a cross-repo signing lock, for example `/tmp/akmarinov-ci-signing.lock`, so multiple App Store jobs do not mutate keychains/profiles concurrently.
   - Use a temporary keychain per run, save original keychain search list, and restore/delete in `if: always()` cleanup.
   - If replacing `ruby/setup-ruby`, validate Ruby with `ruby -rsocket -e 'exit'`; failed local Ruby builds can miss the `socket` extension.
   - If reusing another runner's Ruby toolcache, require both `bin/ruby` and the sibling `.complete` marker before symlinking. Without `.complete`, setup can race an incomplete install.
   - If `actionlint` is unavailable, still parse workflow YAML with Ruby or Python and run `ruby -c fastlane/Fastfile`.

   Minimal self-hosted Ruby fallback check:

   ```bash
   if [ -x "$RUBY_DIR/bin/ruby" ] &&
      [ -f "$RUBY_DIR.complete" ] &&
      "$RUBY_DIR/bin/ruby" -rsocket -e 'exit' >/dev/null 2>&1; then
     echo "$RUBY_DIR/bin" >> "$GITHUB_PATH"
   fi
   ```

11. **App Store upload on main**

   When the desired behavior is "upload to App Store Connect on every push to `main`", make that path explicit:

   - Trigger on `push.branches: [main]`.
   - Run the App Store upload lane from the push path.
   - Keep TestFlight lanes available for manual dispatch if needed.
   - Use `submit_for_review: false` and `automatic_release: false` unless the user explicitly wants automatic review submission/release.
   - If App Store Connect rejects an upload because a marketing version was already used, bump `MARKETING_VERSION`; incrementing only the build number is not enough for a version that has already shipped.

## Verification

Remote GitHub Actions verification:

```bash
GH_TOKEN="$token" gh run list \
  --repo OWNER/APP_REPO \
  --branch main \
  --workflow app-store-deploy.yml \
  --limit 5 \
  --json databaseId,status,conclusion,headSha,createdAt,url,event,displayTitle

GH_TOKEN="$token" gh run watch RUN_ID --repo OWNER/APP_REPO --exit-status
GH_TOKEN="$token" gh run view RUN_ID --repo OWNER/APP_REPO --log |
  rg -n "GITHUB_RUN_NUMBER|Updated CFBundleVersion|xcode_path|Ready to upload|Successfully uploaded package|Successfully uploaded the new binary"
```

App Store Connect verification:

```bash
asc builds list --app "$APP_ID" --platform IOS --output json --paginate |
  jq -r '.data[] | [.id, (.attributes.version // ""), (.attributes.buildNumber // ""), (.attributes.processingState // ""), (.attributes.uploadedDate // "")] | @tsv' |
  head -20
```

Success means:

- latest push-triggered GitHub run is `success`,
- log contains `Successfully uploaded the new binary to App Store Connect`,
- ASC shows the new build number as `VALID` or processing,
- local `main` is clean and matches `origin/main`.

## Troubleshooting Map

- `curl`/Spaceship `401` in a custom preflight: remove brittle App Store network preflight and let fastlane validate the API key.
- GitHub match repo `400`: reset `MATCH_GIT_BASIC_AUTHORIZATION`; ensure no trailing `%` and use `Authorization: Basic <base64>`.
- `Invalid password passed via 'MATCH_PASSWORD'`: the match repo is encrypted with a different password than the app repo secret. You cannot recover the secret from GitHub; align the secret or import assets with the app repo's intended match password.
- Apple distribution certificate limit reached: do not keep retrying mutable `match`; use read-only signing with existing assets, import an existing cert/profile, or ask before revoking/freeing a certificate slot.
- `Certificate '<hash>' is not available on the Developer Portal`: match repo has stale/wrong certificate filenames; ensure cert files are named by portal cert id.
- `No profiles for '<bundle id>' were found` and it asks for development profiles: Release target signing is still Automatic/development; set Release to manual App Store profile.
- Upload rejected for old SDK: use `macos-26` and Xcode 26+.
- Upload rejected because version already exists: bump `MARKETING_VERSION` in the Xcode project or XcodeGen config, then rerun.
- Fastlane says both `api_key` and `api_key_path` are present: clear `APP_STORE_CONNECT_API_KEY_PATH` and `DELIVER_API_KEY_PATH` before calling `deliver`/`upload_to_app_store` with `api_key:`.
- `errSecInternalComponent` on self-hosted runner: private-key access is blocked; use interactive runner or switch to match.
- Compliance warning for encryption: add `ITSAppUsesNonExemptEncryption=false` to the app `Info.plist` when true for the app.
