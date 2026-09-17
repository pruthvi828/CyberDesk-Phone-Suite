# 🚀 Open-Source Daily Contribution Briefing (2026-09-17)

> **Safety Protocol:** These opportunities were vetted for active maintainers and verified beginner-friendly.
> No automated PRs have been submitted. Review and clone locally before contributing.

---

## 1. [CyberSunil/LLMVault](https://github.com/CyberSunil/LLMVault/issues/27) ⭐ 316 Stars
**Language:** `Python` | **Labels:** `help wanted`, `good first issue`, `priority`
**Description:** An intentionally vulnerable OWASP LLM Top 10 training platform for AI Security, Prompt Injection, RAG Security, Agent Security, and GenAI penetration testing.

### 📋 Issue #27: Verify the player name is escaped before it reaches the SVG card
[Open Issue on GitHub](https://github.com/CyberSunil/LLMVault/issues/27)

```markdown
/api/setname accepts any string up to 14 chars with no character filtering, and it flows into card_svg.render() and into /card.svg, which is served as image/svg+xml. If card_svg.py interpolates the name without escaping, a name containing markup would be injected into the rendered SVG. Check whether escaping happens; if not, add it, and add a test covering a name with <, > and &.

Files: card_svg....
```

#### 🛠️ Quick Local Start:
```bash
git clone https://github.com/CyberSunil/LLMVault.git
cd LLMVault
git checkout -b fix-issue-27
```

---

## 2. [CyberSunil/LLMVault](https://github.com/CyberSunil/LLMVault/issues/29) ⭐ 316 Stars
**Language:** `Python` | **Labels:** `help wanted`, `good first issue`
**Description:** An intentionally vulnerable OWASP LLM Top 10 training platform for AI Security, Prompt Injection, RAG Security, Agent Security, and GenAI penetration testing.

### 📋 Issue #29: save_progress() rewrites the whole file on every request
[Open Issue on GitHub](https://github.com/CyberSunil/LLMVault/issues/29)

```markdown
Every chat turn, hint, and live message serialises all sessions and rewrites progress.json. Fine for one player, but the scoreboard is shared, so a classroom or workshop hitting one instance will feel it. Investigate batching writes or only persisting on state-changing events.

File: app.py...
```

#### 🛠️ Quick Local Start:
```bash
git clone https://github.com/CyberSunil/LLMVault.git
cd LLMVault
git checkout -b fix-issue-29
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
