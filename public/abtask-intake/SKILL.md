---
name: abtask-intake
description: "Azure Boards /abtask intake and planning workflow. Use when a user provides an Azure Boards work item ID or URL and wants: worktree + branch setup, work item summary, repository reconnaissance, and an approval-ready implementation plan before any code changes."
---

# Abtask Intake

## Overview

Run the standardized /abtask intake flow: isolate work in a worktree/branch, pull Azure Boards details, scan the repo for relevant context, and deliver a structured plan that requires explicit approval before implementation.

## Workflow

Follow these steps in order; stop for approval before any code edits.

### 0) Parse the work item ID(s)

- Accept either raw numeric IDs or full Azure Boards URLs.
- Always extract numeric IDs and use them everywhere (AB#<id>).
- If multiple IDs/URLs are provided in the same request, treat them as a single intake:
  - Use one worktree and one branch for the combined effort.
  - Keep all IDs in scope for reconnaissance, planning, and PR/commit references.
- Reflect any extra user constraints in assumptions.

### 1) Git hygiene + worktree setup (single worktree for all IDs)

- Check for a clean worktree: `git status --short`.
- If dirty, stash everything: `git stash push -u -m "abtask-<id-or-url>"`.
- Create or reuse a worktree for the combined effort:
  - Branch naming for features/bugs: `users/andreym/{ticketNumber}-some-short-explanation` (example: `users/andreym/1111-localization`).
  - Prefer branch/worktree naming specified by the user’s /abtask instructions.
  - If a system policy mandates a prefix, apply it while preserving the ID(s).
  - Use a stable identifier for naming (recommendation: the first ID, e.g., `users/andreym/<firstId>-<short-description>` and `../<repo>-task-<firstId>`), but keep all IDs in scope in commits/PR metadata.
- After creating/focusing the worktree, copy local helper/config files from the source checkout into the new worktree (when present):
  - `cp <source-repo>/AGENTS.md <worktree>/AGENTS.md`
  - `cp <source-repo>/Kylee/Configuration.xcconfig <worktree>/Kylee/Configuration.xcconfig`
  - Use conditional copies (`[ -f ... ] && cp ...`) so missing local files do not fail the flow.
- Ensure the session CWD is set to the worktree before continuing.

### 2) Fetch the Azure Boards item(s)

- If `az` calls fail, run:
  - `az devops configure --defaults organization=https://dev.azure.com/TCMD project=Andromeda`
- Fetch each work item (expand relations):
  - `az boards work-item show --id <id> --expand relations --output json`

### 3) Summarize work item details (for each ID)

- Title, Type, State, Priority.
- Assignee, Iteration, Tags.
- Acceptance criteria / repro steps (if present).
- Related links (parent, blockers, PRs, design docs).
- Call out missing metadata or ambiguities.
- Note dependencies or conflicts between items (if any).

### 4) Repository reconnaissance

- Use `rg`, `git log -S`, and targeted file searches to locate relevant areas.
- Note impacted modules, owners (if visible), and recent commits.
- Capture risks or open questions for planning across all items.

### 5) Produce the approval-ready plan (covers all IDs)

- Use `update_plan` with multi-step statuses (no single-step plans).
- Provide a structured narrative:
  1. Problem/feature summary + assumptions
  2. Proposed solution + rationale + alternatives
  3. Impacted files/components (concrete)
  4. Test plan (unit/UI, fixtures, success criteria)
  5. Telemetry/flags/migrations/rollout + AB#<id> for every ID in commits/PR, including planned PR title format `{ticket type} #{ticket number}: {name of story}`
- Pause for explicit approval (`approve` / `approve with changes: ...`).

### 6) Post-approval guardrails (for reference)

- Implement in small commits on the chosen branch.
- Use `Kylee-dev` scheme for builds/tests if relevant.
- If creating PRs, use title format `{ticket type} #{ticket number}: {name of story}`.
- For `{ticket type}`, use the Azure DevOps ticket type when available (for example: `Infra`, `Feature`, `Bug`).
- For `{ticket number}`, include all relevant Azure DevOps ticket numbers when multiple items are in scope.
- When multiple ticket numbers are present in the title, use space-separated IDs with no commas (example: `Bug #1234 #5678: Fix login crash`).
- Ensure both User Story and related task tickets are linked in the PR.
- Use markdown description based on `docs/pull_request_template.md` and link AB#<id>.
