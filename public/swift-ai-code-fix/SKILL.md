---
name: swift-ai-code-fix
description: Fix and modernize AI-generated Swift/SwiftUI code for iOS 18+ targets. Use when reviewing or refactoring LLM output (Claude/Codex/Gemini) for deprecated APIs, SwiftUI best practices, accessibility, SwiftData/CloudKit constraints, Swift concurrency misuse, and modern navigation/tab/font patterns.
---

# Swift AI Code Fix

## Overview

Use this skill to audit LLM-generated Swift/SwiftUI code and apply a targeted modernization pass for iOS 18+ (or 26+ where noted). Focus on deprecations, accessibility, performance, and concurrency correctness.

## Workflow

1. Confirm platform targets and constraints
- Assume iOS 18+ unless told otherwise.
- If the user targets iOS 15–17, keep compatibility alternatives and avoid iOS 18+ APIs where required.
- Ask if CloudKit is used when SwiftData models contain uniqueness constraints.

2. Run a fast modernization sweep
- Replace deprecated view modifiers and legacy navigation/tab APIs.
- Convert tap gestures to Buttons for accessibility unless location/tap count is needed.
- Swap ObservableObject for @Observable unless Combine publishers are required.
- Prefer modern URL, image rendering, and sleep APIs.

3. Review structure and performance
- Split computed-property view fragments into their own SwiftUI View types when using @Observable.
- Reduce GeometryReader usage and fixed frames.
- Avoid many types in a single file to keep build times reasonable.

4. Validate behavior and API existence
- Cross-check any unfamiliar APIs against current SDK docs.
- Avoid hallucinated methods or incorrect signatures.

## Fix Checklist (Apply When Seen)

### SwiftUI view modifiers and styling
- Replace `foregroundColor(...)` → `foregroundStyle(...)`.
- Replace `cornerRadius(...)` → `clipShape(.rect(cornerRadius: ...))`.
- Replace `onChange(of:perform:)` 1-parameter variant with 0- or 2-parameter forms.
- Replace excessive `fontWeight(...)` usage; prefer `bold()` when appropriate and use Dynamic Type fonts.
- Replace explicit `.font(.system(size: ...))` with Dynamic Type fonts; for iOS 26+ consider `.font(.body.scaled(by: ...))`.

### Navigation and tabs
- Replace `NavigationView` → `NavigationStack` unless iOS 15 support is required.
- Replace inline destination `NavigationLink` in lists with `navigationDestination(for:)` or equivalent.
- Replace legacy `tabItem(...)` with the new `Tab` API for type-safe selection and modern tab layouts.

### Accessibility and interaction
- Replace `onTapGesture` with `Button` unless tap location or tap count is required.
- Replace image-only buttons or `Label`-only button labels with inline `Button("Title", systemImage: ...)` when possible.

### Data, models, and SwiftData
- Replace `ObservableObject` → `@Observable` unless Combine publishers are required.
- Avoid `@Attribute(.unique)` in SwiftData models when using CloudKit.
- Split view code out of computed properties into dedicated View structs to preserve @Observable invalidation.

### Iteration and collections
- Replace `ForEach(Array(x.enumerated()), id: \.element.id)` → `ForEach(x.enumerated(), id: \.element.id)`.

### Files, timing, and rendering
- Replace documents directory boilerplate with `URL.documentsDirectory`.
- Replace `Task.sleep(nanoseconds:)` with `Task.sleep(for: .seconds(...))`.
- Replace `UIGraphicsImageRenderer` with `ImageRenderer` for SwiftUI view rendering.

### Concurrency and main actor usage
- Remove overuse of `DispatchQueue.main.async`; prefer structured concurrency and `@MainActor` where needed.
- Avoid adding `@MainActor` redundantly for new app templates where main actor isolation is default.

### Layout
- Treat `GeometryReader` as a last resort; prefer `containerRelativeFrame()` and `visualEffect()` or other layout APIs.
- Remove unnecessary fixed frames that fight SwiftUI layout.

### Numeric formatting
- Replace C-style formatting with format styles, e.g. `Text(abs(x), format: .number.precision(.fractionLength(2)))`.

### File organization
- Split large files containing many types to reduce build times and improve navigation.

## Output Expectations

- Provide a concise list of fixes applied or recommended.
- Call out any compatibility constraints (iOS version, CloudKit, Combine requirements).
- If the code uses unknown APIs, explicitly request confirmation or docs before proceeding.
