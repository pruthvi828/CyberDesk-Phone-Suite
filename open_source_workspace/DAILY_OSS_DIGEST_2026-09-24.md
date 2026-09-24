# 🚀 Open-Source Daily Contribution Briefing (2026-09-24)

> **Safety Protocol:** These opportunities were vetted for active maintainers and verified beginner-friendly.
> No automated PRs have been submitted. Review and clone locally before contributing.

---

## 1. [repowise-dev/repowise](https://github.com/repowise-dev/repowise/issues/2222) ⭐ 7,000 Stars
**Language:** `Python` | **Labels:** `bug`, `help wanted`, `good first issue`
**Description:** Codebase intelligence for AI and humans: code health scores, auto-generated docs, git analytics, dead code detection, and architectural decisions via MCP.

### 📋 Issue #2222: [Bug] Telemetry flusher causes console window to flash on Windows during VS Code index updates
[Open Issue on GitHub](https://github.com/repowise-dev/repowise/issues/2222)

```markdown
## Describe the Bug

On Windows, Repowise causes a console window to briefly appear when telemetry is enabled.

This is especially noticeable during automatic index updates triggered by the VS Code extension, where a console window flashes even though the update is supposed to run in the background.

Disabling telemetry fixes the issue completely:

```powershell
repowise telemetry disable
```

Aft...
```

#### 🛠️ Quick Local Start:
```bash
git clone https://github.com/repowise-dev/repowise.git
cd repowise
git checkout -b fix-issue-2222
```

---

## 2. [fivetran/great_expectations](https://github.com/fivetran/great_expectations/issues/12189) ⭐ 11,836 Stars
**Language:** `Python` | **Labels:** `help wanted`, `good first issue`, `maintenance`, `ready-for-work`
**Description:** Always know what to expect from your data.

### 📋 Issue #12189: [MAINTENANCE] Add @override at the 106 sites mypy flags in the excluded library modules
[Open Issue on GitHub](https://github.com/fivetran/great_expectations/issues/12189)

```markdown
Part of #12188.

## What to do

Add the `@override` decorator at every method mypy flags with `explicit-override` in the 45
library modules currently excluded from the type-check — 106 sites in 41 files — and change
nothing else. Import it from `great_expectations.compatibility.typing_extensions`, never from
`typing_extensions` directly (ruff's banned-API rule rejects the direct import).

This is ...
```

#### 🛠️ Quick Local Start:
```bash
git clone https://github.com/fivetran/great_expectations.git
cd great_expectations
git checkout -b fix-issue-12189
```

---
