# Release and notarization notes

## Notarization requirements
- Install Xcode Command Line Tools (for `xcrun` and `notarytool`).
- Provide App Store Connect API credentials:
  - `APP_STORE_CONNECT_API_KEY_P8`
  - `APP_STORE_CONNECT_KEY_ID`
  - `APP_STORE_CONNECT_ISSUER_ID`
- Provide a Developer ID Application identity in `APP_IDENTITY`.

## Sparkle appcast (optional)
- Install Sparkle tools so `generate_appcast` is on PATH.
- Provide `SPARKLE_PRIVATE_KEY_FILE` (ed25519 key).
- The appcast script uses your zip artifact to create an updated `appcast.xml`.
