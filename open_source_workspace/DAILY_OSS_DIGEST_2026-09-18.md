# 🚀 Open-Source Daily Contribution Briefing (2026-09-18)

> **Safety Protocol:** These opportunities were vetted for active maintainers and verified beginner-friendly.
> No automated PRs have been submitted. Review and clone locally before contributing.

---

## 1. [LMCache/LMCache](https://github.com/LMCache/LMCache/issues/5178) ⭐ 11,857 Stars
**Language:** `Python` | **Labels:** `good first issue`, `help wanted`
**Description:** LMCache: Supercharge Your LLM with the Fastest KV Cache Layer

### 📋 Issue #5178: [good-first-issue] buildkite: convert async_request logging to %-format
[Open Issue on GitHub](https://github.com/LMCache/LMCache/issues/5178)

```markdown
Follow-up for #5118 after #5125.

#5125 enabled Ruff `G004` repo-wide and added temporary `per-file-ignores` for the files/directories that still build logging messages with f-strings. This issue is one small slice of that cleanup queue.

Claiming: please comment `/claim` and wait for assignment so we avoid duplicate PRs.

## Scope

Convert only the logging f-strings in:

- `.buildkite/correctness...
```

#### 🛠️ Quick Local Start:
```bash
git clone https://github.com/LMCache/LMCache.git
cd LMCache
git checkout -b fix-issue-5178
```

---

## 2. [lightly-ai/lightly-studio](https://github.com/lightly-ai/lightly-studio/issues/2414) ⭐ 889 Stars
**Language:** `Python` | **Labels:** `bug`, `good first issue`, `help wanted`
**Description:** LightlyStudio - The Unified Data Platform for Multimodal ML

### 📋 Issue #2414: [BUG] Distribution view: `Values` input uses a larger font than other inputs
[Open Issue on GitHub](https://github.com/lightly-ai/lightly-studio/issues/2414)

```markdown
### 🧠 Describe the Bug

Input fields in the Distribution view don't share consistent styling. Specifically, the Values input field renders with a larger font size than the other inputs around it, so the group looks visually misaligned. All inputs in this view should use the same typographic styles.

### 🔁 Steps to Reproduce

Index the example metadata dataset, then open the Distribution view and c...
```

#### 🛠️ Quick Local Start:
```bash
git clone https://github.com/lightly-ai/lightly-studio.git
cd lightly-studio
git checkout -b fix-issue-2414
```

---

## 3. [ARPAHLS/skillware](https://github.com/ARPAHLS/skillware/issues/355) ⭐ 71 Stars
**Language:** `Python` | **Labels:** `documentation`, `enhancement`, `good first issue`, `help wanted`, `skill upgrade`
**Description:** A Python framework for modular, self-contained skill management for machines.

### 📋 Issue #355: [Skill Upgrade]: Improve manifest short_description brief lines for agent routing
[Open Issue on GitHub](https://github.com/ARPAHLS/skillware/issues/355)

```markdown
### Skill ID

registry-wide (all bundled skills)

### Current manifest version

_No response_

### Proposed change

Rewrite or tighten `manifest.yaml` **`short_description`** across bundled registry skills so `SkillContext(mode="brief")` gives agents enough signal to **pick the right skill** and **know when to use it** — without loading full `instructions.md`.

Today brief lines appear in:

- `Ski...
```

#### 🛠️ Quick Local Start:
```bash
git clone https://github.com/ARPAHLS/skillware.git
cd skillware
git checkout -b fix-issue-355
```

---
