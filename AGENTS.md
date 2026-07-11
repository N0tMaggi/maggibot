# AGENTS.md

Discord bot ("Maggibot") built on **py-cord** (`discord.Bot`, `discord.ext.commands`). Windows-first project (`.bat` helpers), but runs anywhere Python 3.8+ does.

## Setup

- Copy `.env.example` -> `.env` and fill in `TOKEN`/`OWNER_ID` at minimum.
- `pip install -r requirements.txt` then run `python main.py install` **once** before first start — this generates the JSON config/data files (`config/`, `data/`) that the bot expects. Both directories are gitignored and do not exist after a fresh clone; the bot will error without this step.
- `start.bat` is a watchdog loop (creates `venv`, installs deps, then loops `python main.py`, auto-restarting on crash with a 5s delay). Use it for local dev on Windows instead of calling `python main.py` directly if you want auto-restart.
- `requirements.txt` includes `mysql-connector-python` unconditionally — `handlers/database.py` imports `mysql.connector` at module level even when `DB_TYPE=json` (the default), so this dependency must stay installed regardless of which DB backend is configured.

## Architecture (non-obvious parts)

- **`cogs/` vs `extensions/` — not interchangeable despite similar names:**
  - `cogs/**/*.py` are auto-discovered and loaded at startup by `load_extensions()` in `main.py:132`. It walks the tree recursively and loads every `.py` file as a py-cord extension (module path = file path with `/` → `.`), so each file under `cogs/` must define a top-level `setup(bot)` function.
  - `extensions/` (e.g. `modextensions.py`, `macextension.py`, `protectionextension.py`) are plain helper modules (embed builders, log senders) imported directly by cogs — they are **not** loaded by the extension loader and have no `setup()`.
- Config/data file paths are centralized in `handlers/config.py` (`SERVER_CONFIG_FILE`, `MAC_FILE`, etc.) with generic `load_data`/`save_data` JSON helpers. Add new persisted files there rather than hardcoding paths in cogs.
- The MAC (global ban) system is the only part with a pluggable storage backend: `DB_TYPE` env var (`json` default, `sqlite`, `mysql`) switches `mac_load_bans`/`mac_save_bans`/`mac_load_bypasses`/`mac_save_bypasses` in `handlers/config.py` between the JSON file and `handlers/database.py`. Everything else always uses JSON files.
- `handlers/env.py` getters (`get_owner`, `get_error_log_channel_id`, etc.) raise if the env var is unset/empty — don't assume optional env vars are safe to read directly with `os.getenv` elsewhere without checking existing patterns.
- Logging goes through `handlers/debug.py` (`LogSystem`, `LogDebug`, `LogError`, `LogNetwork`, `LogModeration`) writing to per-category files under `logs/`, not Python's root logger.

## Known inconsistencies (don't "fix" incidentally)

See `docs/ISSUES_SUMMARY.md` / `docs/code_analysis_report.md` for the full audit. Most relevant if touching cogs:
- `create_embed()` is duplicated across ~11 cog files instead of using the centralized `utils/embed_helpers.py::create_embed` (and `utils/colors.py::EmbedColors`). New code should use the `utils` version; existing duplicates are a known-but-unresolved issue, not a bug to silently refactor as a side effect of unrelated changes.
- A few cog filenames are PascalCase (`AntiChannelRaid.py`, `AntiWebhook.py`, `Automod.py`) instead of snake_case — intentional inconsistency, tracked as low-priority cleanup.

## Verification (CI-mirrored, no test suite exists)

There are no unit tests. CI (`.github/workflows/`) runs these checks on push/PR — run them locally before finishing a change:
```
pip install ruff && ruff check . --select F821,E9,F63,F7,F82   # code-quality.yml — only these rule codes are enforced
python -m compileall .                                          # bytecode compile check
pip install "bandit[toml]" && bandit -r . -ll -iii -x .venv,venv # security-scans.yml
pip install pip-audit && pip-audit -r requirements.txt           # dependency audit
```
CodeQL (`.github/workflows/codeql.yml`) runs separately in GitHub Actions only.
