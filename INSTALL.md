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
2. **Install dependencies**
   ```bash
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
   python main.py
   ```

For Windows users there are also `install.bat` and `start.bat` helpers that wrap these commands.
