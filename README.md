<p align="center">
  <h1 align="center">🛡️ MAGGIBOT</h1>
</p>

<p align="center">
  <em>High-performance, modern, modular Discord bot built with Python, Pycord 2.8, and Discord Interactions v2.</em>
</p>

<p align="center">
  <strong>Made by Maggi</strong>
</p>

<p align="center">
  <a href="https://github.com/N0tMaggi/maggibot/blob/main/LICENSE.txt"><img src="https://img.shields.io/badge/License-MIT-ff007a.svg?style=for-the-badge" alt="License"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+"></a>
  <a href="https://github.com/Pycord-Development/pycord"><img src="https://img.shields.io/badge/Pycord-2.8.1-5865F2.svg?style=for-the-badge&logo=discord&logoColor=white" alt="Pycord 2.8.1"></a>
  <a href="https://docs.pytest.org/"><img src="https://img.shields.io/badge/Tests-268%20Passed-00c853.svg?style=for-the-badge&logo=pytest&logoColor=white" alt="Pytest 268 Passed"></a>
  <a href="https://github.com/N0tMaggi/maggibot"><img src="https://img.shields.io/badge/i18n-EN%20%7C%20DE-purple.svg?style=for-the-badge" alt="i18n EN | DE"></a>
</p>

---

## 📑 Table of Contents

- [✨ Overview](#-overview)
- [⚡ Key Features](#-key-features)
- [🎛️ Interactive Setup Dashboard](#️-interactive-setup-dashboard)
- [🍯 Honeypot Protection](#-honeypot-protection)
- [🌐 Localization (i18n)](#-localization-i18n)
- [📁 Architecture & Directory Structure](#-architecture--directory-structure)
- [🚀 Quick Start & Installation](#-quick-start--installation)
- [💾 Database Backends & Docker](#-database-backends--docker)
- [🧪 Testing & Quality Assurance](#-testing--quality-assurance)
- [📜 License](#-license)

---

## ✨ Overview

**MaggiBot** is a modern, modular Discord bot engineered from the ground up for stability, security, and intuitive community management. Powered by **Pycord 2.8.1** and Discord's latest UI components (**Interactions v2**), MaggiBot replaces legacy text-command clutter with interactive dashboards, persistent selects, toggle buttons, and modal dialogs.

Designed with **multi-server scalability** and **containerized deployments (Docker)** in mind, MaggiBot supports multiple database backends (SQLite, MySQL, MongoDB, and JSON fallback) and features a per-server internationalization engine (English & German).

---

## ⚡ Key Features

### 🛡️ Protection & Security Suite
* **🍯 Honeypot Trap Channel**: Dedicated trap channel that catches automated spam bots and compromised accounts, immediately purges spam messages, and applies an automated **3-day tempban** stored in the database with automatic background unban scheduling.
* **⚡ Anti-Spam & Rate Limiter**: Detects message flooding and burst spam, enforcing escalating timeouts.
* **🚨 Anti-Raid**: Automated detection and mitigation of mass-join raids, with auto-kick/ban quarantine capabilities.
* **👻 Anti-GhostPing**: Logs deleted or edited messages containing member/role pings to audit channels.
* **🔒 Emergency Guild Lockdown (`/lockdown`)**: Instant server-wide quarantine toggle for server owners during security incidents.
* **🛡️ Global MAC Ban Network**: Synchronized blacklist network protecting participating servers from known malicious actors.

### 🎛️ Modern Administration & Onboarding
* **🎛️ Interactive `/setup` Dashboard**: All-in-one visual control panel with interactive selects and buttons to configure protection, logging, roles, media rules, and server language with zero config file editing.
* **🎙️ VoiceGate Onboarding**: Dedicated waiting gate for incoming voice users requiring interactive rules acknowledgment before moving them to active voice channels.
* **🖼️ Media-Only Channels (`/onlyimages-enable`)**: Enforces attachment/media posts in designated media channels with instant automated cleanup and user notifications.
* **🏷️ Dynamic Server Tags (`/tag`)**: Fast, rich server macro responses supporting dynamic variables (`{user}`, `{servername}`).

### 📊 Community & Statistics
* **📈 Leveling & XP Engine**: Tracks message activity and voice channel time with multiplier bonuses, anti-grind cooldowns, and level-up direct messages.
* **🏆 Rich Leaderboards**: Beautiful, pageable text and voice leaderboards with custom embed layouts.

### 🎨 Design & Experience
* **🎨 Unified Embed Palette**: Consistent, accessible design system across all 38 modules using standardized semantic color palettes (`EmbedColors`) and safe fallback avatars.

---

## 🎛️ Interactive Setup Dashboard

Configure your entire server with a single command:
```
/setup
```

The setup dashboard provides:
* **Interactive Category Selector**: Switch between *Overview*, *Protection*, *Logging*, *Roles*, *Media*, and *Language*.
* **One-Click Toggle Buttons**: Instant toggles for Anti-Spam, Anti-Raid, Protection Mode, and TikTok Auto-Embed.
* **VoiceGate Rules Modal**: Edit onboarding rules on the fly through a native Discord popup modal.
* **Live Language Switcher**: Seamlessly toggle between English (`en`) and German (`de`) per guild in real-time.

---

## 🍯 Honeypot Protection

The Honeypot module stops automated spam waves in their tracks:

```
/honeypot action:setup
/honeypot-setup [channel:#channel]
/honeypot-remove [delete_channel:True/False]
```

1. **Trap Setup**: Creates or links a dedicated channel (e.g. `🍯・honeypot`) visible to members with a prominent pinned warning embed.
2. **Detection**: Any non-admin user sending a message is caught instantly.
3. **Purge & Ban**: Deletes the spam message, sends a localized direct message notification, purges 1 day of message history, and issues a **3-day tempban**.
4. **Database-Backed Persistence**: Tempban records are stored in the database (SQLite / MySQL / MongoDB), ensuring bans survive bot restarts and container updates.
5. **Background Unban Worker**: An automated task loop runs every minute to unban users once their 3-day penalty expires.

---

## 🌐 Localization (i18n)

MaggiBot includes a full per-server internationalization system:

* **Supported Languages**: English (`en`, default) and German (`de`).
* **Instant Fallbacks**: Missing keys automatically fallback to English, preventing missing text errors.
* **In-Memory Caching**: Fast guild locale cache prevents repetitive database lookups during message traffic.
* **Configurable in `/setup`**: Server administrators can switch languages with a single button click in the dashboard.

```python
from handlers.locale import t

# Automatically uses the guild's chosen language
embed = create_security_embed(
    title=t("honeypot.log_title", guild=guild),
    description=t("honeypot.log_desc", guild=guild, user=user.mention)
)
```

---

## 📁 Architecture & Directory Structure

```sh
└── maggibot/
    ├── cogs/
    │   ├── admin/           # Administrative utilities and feedback
    │   ├── fun/             # Interactive games and utilities
    │   ├── general/         # General info commands (ping, serverinfo, userinfo)
    │   ├── logging/         # Member, message, and voice audit loggers
    │   ├── mac/             # MAC global ban security network
    │   ├── media/           # Media commands and TikTok auto-embeds
    │   ├── misc/            # Additional server utilities
    │   ├── moderation/      # Ban, kick, mute, and community moderation
    │   ├── owner/           # Owner maintenance and global lockdown
    │   ├── protection/      # Honeypot, anti-spam, anti-raid, protection setup
    │   ├── server/          # OnlyImages, tags, and server management
    │   ├── setup/           # Interactive setup dashboard
    │   ├── stats/           # XP, leveling, voice tracking, and leaderboards
    │   ├── system/          # Application command error handling and events
    │   └── verify/          # VoiceGate onboarding system
    ├── handlers/
    │   ├── config.py        # Centralized configuration access
    │   ├── database.py      # Multi-backend database manager (SQLite/MySQL/Mongo/JSON)
    │   ├── debug.py         # Formatted console logging
    │   └── locale.py        # i18n localization engine
    ├── locales/
    │   ├── en.json          # English translations
    │   └── de.json          # German translations
    ├── tests/               # 268 automated unit & integration tests
    │   ├── test_cogs/
    │   ├── test_handlers/
    │   └── test_utils/
    ├── utils/
    │   ├── colors.py        # Standardized Discord color palette
    │   └── embed_helpers.py # Centralized safe embed creators
    ├── main.py              # Application entrypoint & cog loader
    └── requirements.txt     # Python dependencies
```

---

## 🚀 Quick Start & Installation

### Prerequisites
* **Python 3.10 or higher**
* **Git**
* A Discord Bot Token from the [Discord Developer Portal](https://discord.com/developers/applications) with:
  * `SERVER MEMBERS INTENT` enabled
  * `MESSAGE CONTENT INTENT` enabled

### 1. Clone & Setup Environment
```bash
git clone https://github.com/N0tMaggi/maggibot.git
cd maggibot

python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

```env
DISCORD_TOKEN=your_bot_token_here
OWNER_ID=your_discord_user_id
DB_TYPE=sqlite
DB_NAME=data/maggibot.db
```

### 3. Initialize & Run
```bash
# Initialize required directories and default configs
python main.py install

# Start the bot (Windows)
start.bat

# Start the bot (Linux / macOS)
python main.py
```

---

## 💾 Database Backends & Docker

MaggiBot is cloud and container-ready. Set `DB_TYPE` in your `.env`:

| Backend | `DB_TYPE` | Configuration Required | Description |
| :--- | :--- | :--- | :--- |
| **SQLite** | `sqlite` | `SQLITE_PATH` | Zero-setup local relational DB (Default: `data/maggibot.db`) |
| **MySQL** | `mysql` | `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | High-scale relational database |
| **PostgreSQL**| `postgres`| `POSTGRES_URL` or standard PG variables | Enterprise SQL storage |
| **MongoDB** | `mongo` | `MONGO_URI` | Document database for flexible cloud clustering |
| **JSON** | `json` | *(None)* | Flat file storage in `data/` and `config/` |

---

## 🧪 Testing & Quality Assurance

MaggiBot maintains a comprehensive, production-grade test suite using **pytest** and **pytest-asyncio**:

```bash
pytest
```

* **268 passing tests** covering:
  * All 38 cogs and extensions
  * Interactive Setup Dashboard & Modals
  * Multi-backend database CRUD (SQLite, JSON, MySQL)
  * Honeypot 3-day tempban lifecycle and unban background worker
  * Localization engine string interpolation, cache, and fallbacks
  * Rate-limiting, anti-raid, and permission-handling guards
  * Discord embed safety limits and formatting

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE.txt](LICENSE.txt) file for details.

---

<p align="center">
  <b>MaggiBot</b> — Built with ❤️ by Maggi
</p>
