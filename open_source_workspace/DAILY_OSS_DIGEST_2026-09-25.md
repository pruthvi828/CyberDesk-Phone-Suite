# 🚀 Open-Source Daily Contribution Briefing (2026-09-25)

> **Safety Protocol:** These opportunities were vetted for active maintainers and verified beginner-friendly.
> No automated PRs have been submitted. Review and clone locally before contributing.

---

## 1. [wemake-services/django-modern-rest](https://github.com/wemake-services/django-modern-rest/issues/1600) ⭐ 1,472 Stars
**Language:** `Python` | **Labels:** `feature`, `good first issue`, `help wanted`, `opensource september`
**Description:** Modern REST framework for Django with types and async support!

### 📋 Issue #1600: `_validate_throttling` check is a bad design :(
[Open Issue on GitHub](https://github.com/wemake-services/django-modern-rest/issues/1600)

```markdown
This code https://github.com/wemake-services/django-modern-rest/blob/6649d058e5e9580be90e8ee3cee4f540c0962382/dmr/validation/endpoint_metadata.py#L934-L971

knows a lot about specific backends for throttling. But, why do we do this in metadata validation? Why don't we create `.validate` method in `throttling` (and `auth` just in case) objects instead? 

Like we do for `parser` and `renderer` objec...
```

#### 🛠️ Quick Local Start:
```bash
git clone https://github.com/wemake-services/django-modern-rest.git
cd django-modern-rest
git checkout -b fix-issue-1600
```

---

## 2. [MakazhanAlpamys/Soup](https://github.com/MakazhanAlpamys/Soup/issues/1267) ⭐ 7,161 Stars
**Language:** `Python` | **Labels:** `bug`, `help wanted`, `good first issue`
**Description:** Fine-tune LLMs from one YAML. Layer streaming trains an 8B model on a 4 GB laptop GPU.

### 📋 Issue #1267: The error mapper treats any `401` / `403` digits as an auth failure: `soup train` reports a too-long row 401 as "Authentication failed." and hides the real message
[Open Issue on GitHub](https://github.com/MakazhanAlpamys/Soup/issues/1267)

```markdown
## What happens

`soup` sends every uncaught exception through `format_friendly_error`, which tests each entry of `ERROR_MAP` as a plain substring of the message. Two entries are the bare strings `"401"` and `"403"`. Any message that merely contains those digits is reported as an authentication or permission failure, and the canned text replaces the real message. That includes a row number, a te...
```

#### 🛠️ Quick Local Start:
```bash
git clone https://github.com/MakazhanAlpamys/Soup.git
cd Soup
git checkout -b fix-issue-1267
```

---

## 3. [Berserk-hub150/skillhawk](https://github.com/Berserk-hub150/skillhawk/issues/163) ⭐ 64 Stars
**Language:** `JavaScript` | **Labels:** `enhancement`, `help wanted`, `good first issue`, `community`, `low hanging fruit`, `up-for-grabs`, `first-timers-only`, `micro-contribution`, `type: task`, `beginner-friendly`, `hacktoberfest`, `category:fixtures`
**Description:** Catch dangerous AI agent skills before they catch you. Zero-dependency security scanner for Agent Skills, SKILL.md and MCP configs.

### 📋 Issue #163: [Good First Issue] Add a safe-fixture writing tip [MC-007]
[Open Issue on GitHub](https://github.com/Berserk-hub150/skillhawk/issues/163)

```markdown
<!-- skillhawk-task:MC-007 -->
<!-- automated-by:skillhawk-community-factory -->
## Add a safe-fixture writing tip

> **Browser-only · 2–5 minutes · beginner-friendly · no local setup required**

### Your task

Add the prepared contributor note below.

Create `community/micro-contributions/contributor-notes/safe-fixture-writing.json`:

```json
{
  "topic": "Safe fixture writing",
  "tip": "A safe ...
```

#### 🛠️ Quick Local Start:
```bash
git clone https://github.com/Berserk-hub150/skillhawk.git
cd skillhawk
git checkout -b fix-issue-163
```

---
