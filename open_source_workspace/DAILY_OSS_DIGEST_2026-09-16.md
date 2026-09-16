# 🚀 Open-Source Daily Contribution Briefing (2026-09-16)

> **Safety Protocol:** These opportunities were vetted for active maintainers and verified beginner-friendly.
> No automated PRs have been submitted. Review and clone locally before contributing.

---

## 1. [Lyellr88/marm-memory](https://github.com/Lyellr88/marm-memory/issues/201) ⭐ 380 Stars
**Language:** `Python` | **Labels:** `bug`, `help wanted`, `good first issue`
**Description:** Local-first 3-in-1 AI memory layer & MCP server for Claude Code, Codex, Grok, Gemini, VS Code and Cursor. Fuses session history, codebase indexing & concept graphs in SQLite. Enables zero-cloud, privacy-first context & instant recall, supports multi-agent swarms.

### 📋 Issue #201: Code graph auto-indexing never runs in Docker
[Open Issue on GitHub](https://github.com/Lyellr88/marm-memory/issues/201)

```markdown
## Summary

Code graph auto-indexing never activates in the Docker image, despite the image shipping a working codebase-memory engine for manual graph tools.

## Evidence

`marm_mcp_server/core/graph_index_worker.py::binary_present()` only checks the pip-managed engine location:

```python
from codebase_memory_mcp import _cli
return bool(_cli._bin_path(_cli._version()).exists())
```

The Docker im...
```

#### 🛠️ Quick Local Start:
```bash
git clone https://github.com/Lyellr88/marm-memory.git
cd marm-memory
git checkout -b fix-issue-201
```

---

## 2. [hybridops-tech/hybridops-core](https://github.com/hybridops-tech/hybridops-core/issues/260) ⭐ 358 Stars
**Language:** `Python` | **Labels:** `bug`, `good first issue`, `help wanted`, `testing`
**Description:** Community edition of HybridOps. A platform exploring contract-driven automation for hybrid infrastructure.

### 📋 Issue #260: [bug] Blueprint validation ignores misplaced step settings
[Open Issue on GitHub](https://github.com/hybridops-tech/hybridops-core/issues/260)

```markdown
### Area

Module or blueprint

### Relevant reference

`networking/edge-control-plane@v1`

### Expected behaviour

Blueprint validation should reject settings that are not part of the step contract. The error should name the step and the unexpected keys.

### Observed behaviour

The `shared_control_host` step has `firewall_name`, `ssh_source_cidrs`, and `firewall_extra_tcp_ports` beside `inputs` r...
```

#### 🛠️ Quick Local Start:
```bash
git clone https://github.com/hybridops-tech/hybridops-core.git
cd hybridops-core
git checkout -b fix-issue-260
```

---

## 3. [ARPAHLS/skillware](https://github.com/ARPAHLS/skillware/issues/355) ⭐ 70 Stars
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
