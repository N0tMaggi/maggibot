# Installation Guide

This document describes how to install, configure, and run **MaggiBot** locally or via Docker.

## Prerequisites

- Python 3.10 or higher
- `pip` package manager
- Discord Bot Token with Server Members and Message Content Privileged Gateway Intents enabled in the [Discord Developer Portal](https://discord.com/developers/applications)

## Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/N0tMaggi/maggibot.git
   cd maggibot
   ```

2. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux / macOS
   source venv/bin/activate

   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Open `.env` and fill in:
     - `DISCORD_TOKEN`: Your bot application token.
     - `OWNER_ID`: Your Discord user ID.
     - `DB_TYPE`: `sqlite`, `mysql`, `mongo`, or `json` (default).

4. **Initialize Configs**
   Run the setup helper once to generate default configuration directories and files:
   ```bash
   python main.py install
   ```

5. **Start the Bot**
   ```bash
   # Windows
   start.bat
   # Linux / macOS
   python main.py
   ```

## Database Configuration

MaggiBot supports multi-backend database integration for multi-platform and Docker deployment:

- **JSON (`DB_TYPE=json`)**: Zero configuration file-based storage in `data/` and `config/`.
- **SQLite (`DB_TYPE=sqlite`)**: Lightweight relational database. Configure `SQLITE_PATH=data/maggibot.db`.
- **MySQL (`DB_TYPE=mysql`)**: Provide `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME`.
- **MongoDB (`DB_TYPE=mongo`)**: Provide `MONGO_URI` (e.g. `mongodb://localhost:27017/maggibot`).

## Running Tests

Run the full automated test suite (268 unit and integration tests):
```bash
pytest
```
