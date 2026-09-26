# 🚀 Open-Source Daily Contribution Briefing (2026-09-26)

> **Safety Protocol:** These opportunities were vetted for active maintainers and verified beginner-friendly.
> No automated PRs have been submitted. Review and clone locally before contributing.

---

## 1. [fossasia/voxbento](https://github.com/fossasia/voxbento/issues/544) ⭐ 1,508 Stars
**Language:** `Python` | **Labels:** `help wanted`, `good first issue`
**Description:** Open Source AI powered Interpretation Platform https://voxbento.com

### 📋 Issue #544: Admin User Detail: Format timestamps in a human-readable way
[Open Issue on GitHub](https://github.com/fossasia/voxbento/issues/544)

```markdown
Timestamps across admin pages (like `created_at` in `user_list.html` and `event_list.html`) are formatted as `YYYY-MM-DD` or `YYYY-MM-DD HH:MM`. This is a bit rigid.

**Task:**
Change the strftime formatting in the Jinja templates to a more readable format, such as `Jan 1, 2026` or `Jan 1, 2026, 14:30`....
```

#### 🛠️ Quick Local Start:
```bash
git clone https://github.com/fossasia/voxbento.git
cd voxbento
git checkout -b fix-issue-544
```

---

## 2. [WesternFriend/westernfriend.org](https://github.com/WesternFriend/westernfriend.org/issues/1211) ⭐ 63 Stars
**Language:** `Python` | **Labels:** `help wanted`, `good first issue`, `hacktoberfest`
**Description:** A website for Western Friend (westernfriend.org), a Quaker publication that provides resources and support for Quaker communities and individuals seeking to live out their faith in the world. Western Friend is part of the Religious Society of Friends.

### 📋 Issue #1211: Migrate legacy EMAIL_* settings to Django's MAILERS setting
[Open Issue on GitHub](https://github.com/WesternFriend/westernfriend.org/issues/1211)

```markdown
## Summary

Django 6.1 deprecates the legacy `EMAIL_*` settings in favor of the new `MAILERS` setting, ahead of removal in Django 7.0. Upgrading dependencies (see recent "Upgrade dependencies" commit, which bumped Django 6.0.4 -> 6.1.1) surfaced these warnings in the test suite:

```
RemovedInDjango70Warning: The EMAIL_BACKEND setting is deprecated. Migrate to MAILERS before Django 7.0.
RemovedInD...
```

#### 🛠️ Quick Local Start:
```bash
git clone https://github.com/WesternFriend/westernfriend.org.git
cd westernfriend.org
git checkout -b fix-issue-1211
```

---

## 3. [fossasia/voxbento](https://github.com/fossasia/voxbento/issues/576) ⭐ 1,508 Stars
**Language:** `Python` | **Labels:** `help wanted`, `good first issue`
**Description:** Open Source AI powered Interpretation Platform https://voxbento.com

### 📋 Issue #576: Clean up: Remove unused configuration variables
[Open Issue on GitHub](https://github.com/fossasia/voxbento/issues/576)

```markdown
**Overview**
The `effective_mediamtx_internal_base` property and `supertonic_base_url` variable in `portal/config.py` (`Settings` class) are not used by any application logic.

**Action Item**
Remove these variables from the configuration schema....
```

#### 🛠️ Quick Local Start:
```bash
git clone https://github.com/fossasia/voxbento.git
cd voxbento
git checkout -b fix-issue-576
```

---
