# Installation Guide

This document describes how to install and run **Maggibot** locally.

## Prerequisites

- Python 3.8 or higher
- `pip` package manager

## Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/ag7dev/maggibot
   cd maggibot
   ```
2. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv venv
   venv\Scripts\activate    # on Windows
   source venv/bin/activate # on Linux/macOS
   pip install -r requirements.txt
   ```
3. **Create your configuration**
   - Copy `.env.example` to `.env` and fill in the required values (bot token, owner ID, etc.).
   - Run the setup helper once to generate default config files:
     ```bash
     python main.py install
     ```
4. **Start the bot**
   ```bash
   start.bat  # Windows
   ./start.sh # Linux/macOS
   # or
   python main.py
   ```

### Linux/macOS helper scripts

- `./install.sh` creates a local `.venv/`, installs dependencies and runs `python main.py install`.
- `./start.sh` creates/uses `.venv/`, installs dependencies and starts the bot.

For Windows users there are also `install.bat` and `start.bat` helpers that wrap these commands.

## Database Configuration (Optional)

By default, Maggibot uses a JSON file (`data/mac.json`) to store MAC ban data. You can optionally configure it to use a MySQL or SQLite database instead.

1.  **Choose your database type:**
    *   In your `.env` file, set `DB_TYPE` to one of the following:
        *   `json` (default): Uses the `mac.json` file.
        *   `sqlite`: Uses a local SQLite database file.
        *   `mysql`: Uses a remote or local MySQL server.

2.  **Configure credentials:**
    *   **For `sqlite`:**
        *   Set `DB_NAME` to the desired path for your database file (e.g., `data/maggibot.db`).
    *   **For `mysql`:**
        *   `DB_HOST`: The hostname or IP address of your MySQL server.
        *   `DB_USER`: The username for the database.
        *   `DB_PASSWORD`: The password for the database user.
        *   `DB_NAME`: The name of the database to use.

3.  **Migrate existing data (if any):**
    *   If you have existing bans in `data/mac.json`, you can migrate them to your database by running the migration script:
      ```bash
      python migrate_mac_json_to_db.py
      ```
    *   This will generate a `mac_bans.sql` file. You can then import this file into your database. For SQLite, the script will automatically create and populate the database.
