<p align="center">
    <img src="https://img.icons8.com/external-tal-revivo-regular-tal-revivo/96/external-readme-is-a-easy-to-build-a-developer-hub-that-adapts-to-the-user-logo-regular-tal-revivo.png" align="center" width="30%">
</p>
<p align="center"><h1 align="center">MAGGIBOT</h1></p>
<p align="center">
	<em><code>â¯ Made by Maggi</code></em>
</p>
<p align="center">
	<img src="https://img.shields.io/github/license/ag7dev/maggibot?style=flat&logo=opensourceinitiative&logoColor=white&color=ff00e0" alt="license">
	<img src="https://img.shields.io/github/last-commit/ag7dev/maggibot?style=flat&logo=git&logoColor=white&color=ff00e0" alt="last-commit">
	<img src="https://img.shields.io/github/languages/top/ag7dev/maggibot?style=flat&color=ff00e0" alt="repo-top-language">
	<img src="https://img.shields.io/github/languages/count/ag7dev/maggibot?style=flat&color=ff00e0" alt="repo-language-count">
</p>
<p align="center">Built with the tools and technologies:</p>
<p align="center">
	<img src="https://img.shields.io/badge/JSON-000000.svg?style=flat&logo=JSON&logoColor=white" alt="JSON">
	<img src="https://img.shields.io/badge/Python-3776AB.svg?style=flat&logo=Python&logoColor=white" alt="Python">
	<img src="https://img.shields.io/badge/Discord-5865F2.svg?style=flat&logo=Discord&logoColor=white" alt="Discord">
</p>
<br>

## ðŸ”— Table of Contents

- [ðŸ“ Overview](#-overview)
- [ðŸ‘¾ Features](#-features)
- [ðŸ“ Project Structure](#-project-structure)
  - [ðŸ“‚ Project Index](#-project-index)
- [ðŸš€ Getting Started](#-getting-started)
  - [â˜‘ï¸ Prerequisites](#-prerequisites)
  - [âš™ï¸ Installation](#-installation)
  - [ðŸ¤– Usage](#ðŸ¤–-usage)
  - [ðŸ§ª Testing](#ðŸ§ª-testing)
## ðŸ” Automated Scanning

GitHub Actions now run automated quality and security scans:

- **Code Quality**: critical Ruff rules (`F821`, `E9`, etc.) and Python bytecode compile checks.
- **Security Scans**: Bandit static security checks and `pip-audit` dependency audits.
- **CodeQL**: weekly and PR/push deep analysis for Python security/code-quality issues.

These workflows live in `.github/workflows/` and run on pull requests and pushes to the default branch.
- [ðŸ“Œ Project Roadmap](#-project-roadmap)
- [ðŸ”° Contributing](#-contributing)
- [ðŸŽ— License](#-license)
- [ðŸ™Œ Acknowledgments](#-acknowledgments)

---

## ðŸ“ Overview

**Maggibot** is a modular Discord bot written in Python using
[`py-cord`](https://github.com/Pycord-Development/pycord). It is designed to be
extended through cogs and provides a wide range of moderation and community
management tools. The bot relies on a small set of configuration and data files
(see [`handlers/config.py`](handlers/config.py)) and can be customised via an
environment file based on `.env.example`.

---

## ðŸ‘¾ Features

- **Administration** â€“ tools like autoroles, configuration commands and voice
  gate management.
- **Moderation** â€“ classic moderation actions (kick, ban, mute) plus community
  voting utilities.
- **Protection** â€“ modules for anti-spam, anti-raid, anti-ghost ping and webhook
  defence.
- **Statistics** â€“ XP and leaderboard system with adjustable multipliers.
- **Ticket system** â€“ simple ticket creation workflow for support channels.
- **Fun and utilities** â€“ quotes, tags, TikTok downloader and more.

---

## ðŸ“ Project Structure

```sh
â””â”€â”€ maggibot/
    â”œâ”€â”€ README.md
    â”œâ”€â”€ assets
    â”‚   â””â”€â”€ All the Mp3 files are stored here
    â”œâ”€â”€ cogs
    â”‚   â””â”€â”€ All Cogs Are Stored here
    â”‚       â””â”€â”€ Including all Files
    â”œâ”€â”€ config
    â”‚   â””â”€â”€ All Config Files Are Stored here
    â”œâ”€â”€ data
    â”‚   â””â”€â”€ All data like stats ans so on are stored here
    â”œâ”€â”€ extensions
    â”‚   â””â”€â”€ All extensions are stored here
    â”œâ”€â”€ handlers
    â”‚   â””â”€â”€ All Handlers are here
    â”œâ”€â”€ main.py
    â”œâ”€â”€ requirements.txt
    â””â”€â”€ start.bat
```


### ðŸ“‚ Project Index
<details open>
	<summary><b><code>MAGGIBOT/</code></b></summary>
	<details> <!-- __root__ Submodule -->
		<summary><b>__root__</b></summary>
		<blockquote>
			<table>
			<tr>
				<td><b><a href='https://github.com/ag7dev/maggibot/blob/master/main.py'>main.py</a></b></td>
				<td><code>â¯ Main entry point of the bot.</code></td>
			</tr>
			<tr>
				<td><b><a href='https://github.com/ag7dev/maggibot/blob/master/requirements.txt'>requirements.txt</a></b></td>
				<td><code>â¯ Required packages for the bot.</code></td>
			</tr>
			<tr>
				<td><b><a href='https://github.com/ag7dev/maggibot/blob/master/start.bat'>start.bat</a></b></td>
				<td><code>â¯ Bat file to start the bot.</code></td>
			</tr>
			</table>
		</blockquote>
	</details>
	<details> <!-- handlers Submodule -->
		<summary><b>handlers</b></summary>
		<blockquote>
			<table>
			<tr>
				<td><b><a href='https://github.com/ag7dev/maggibot/blob/master/handlers/debug.py'>debug.py</a></b></td>
				<td><code>â¯ Debug Handler</code></td>
			</tr>
			<tr>
				<td><b><a href='https://github.com/ag7dev/maggibot/blob/master/handlers/config.py'>config.py</a></b></td>
				<td><code>â¯ Handler for config</code></td>
			</tr>
			<tr>
				<td><b><a href='https://github.com/ag7dev/maggibot/blob/master/handlers/env.py'>env.py</a></b></td>
				<td><code>â¯ env handler</code></td>
			</tr>
			</table>
		</blockquote>
	</details>
	<details> <!-- config Submodule -->
		<summary><b>config</b></summary>
		<blockquote>
			<table>
			<tr>
				<td><b><a href='https://github.com/ag7dev/maggibot/blob/master/config/voicegateconfig.json'>voicegateconfig.json</a></b></td>
				<td><code>â¯ Voicegate config</code></td>
			</tr>
			<tr>
				<td><b><a href='https://github.com/ag7dev/maggibot/blob/master/config/serverconfig.json'>serverconfig.json</a></b></td>
				<td><code>â¯ Serverconfig</code></td>
			</tr>
			<tr>
				<td><b><a href='https://github.com/ag7dev/maggibot/blob/master/config/lockdown.json'>lockdown.json</a></b></td>
				<td><code>â¯ Lockdown config</code></td>
			</tr>
			</table>
		</blockquote>
	</details>
	<details> <!-- extensions Submodule -->
		<summary><b>extensions</b></summary>
		<blockquote>
			<table>
			<tr>
				<td><b><a href='https://github.com/ag7dev/maggibot/blob/master/extensions/modextensions.py'>modextensions.py</a></b></td>
				<td><code>â¯ Mod extensions</code></td>
			</tr>
			<tr>
				<td><b><a href='https://github.com/ag7dev/maggibot/blob/master/extensions/statsextension.py'>statsextension.py</a></b></td>
				<td><code>â¯ Stats extension</code></td>
			</tr>
			</table>
		</blockquote>
	</details>
</details>

---
## ðŸš€ Getting Started

### â˜‘ï¸ Prerequisites

Before getting started with maggibot, ensure your runtime environment meets the following requirements:

- **Programming Language:** Python
- **Package Manager:** Pip


### âš™ï¸ Installation

See [INSTALL.md](INSTALL.md) for a full step-by-step installation guide. In
clone the repository, create a virtual environment with `python -m venv venv`, activate it and install the dependencies with `pip install -r requirements.txt`, copy `.env.example` to `.env` and run `python main.py install` once to create the default configuration files.



### ðŸ¤– Usage
Run Maggibot with the helper script:

Run `start.bat` on Windows or `python main.py` from an activated virtual environment.

---
## ðŸ“Œ Project Roadmap

- [X] **`Task 1`**: <strike>Main Structure.</strike>
- [X] **`Task 2`**: <strike>Installer.</strike>
- [ ] **`Task 3`**: More Protection Features.

---

## ðŸ”° Contributing

- **ðŸ’¬ [Join the Discussions](https://github.com/ag7dev/maggibot/discussions)**: Share your insights, provide feedback, or ask questions.
- **ðŸ› [Report Issues](https://github.com/ag7dev/maggibot/issues)**: Submit bugs found or log feature requests for the `maggibot` project.
- **ðŸ’¡ [Submit Pull Requests](https://github.com/ag7dev/maggibot/blob/main/CONTRIBUTING.md)**: Review open PRs, and submit your own PRs.

<details closed>
<summary>Contributing Guidelines</summary>

1. **Fork the Repository**: Start by forking the project repository to your github account.
2. **Clone Locally**: Clone the forked repository to your local machine using a git client.
   ```sh
   git clone https://github.com/ag7dev/maggibot
   ```
3. **Create a New Branch**: Always work on a new branch, giving it a descriptive name.
   ```sh
   git checkout -b new-feature-x
   ```
4. **Make Your Changes**: Develop and test your changes locally.
5. **Commit Your Changes**: Commit with a clear message describing your updates.
   ```sh
   git commit -m 'Implemented new feature x.'
   ```
6. **Push to github**: Push the changes to your forked repository.
   ```sh
   git push origin new-feature-x
   ```
7. **Submit a Pull Request**: Create a PR against the original project repository. Clearly describe the changes and their motivations.
8. **Review**: Once your PR is reviewed and approved, it will be merged into the main branch. Congratulations on your contribution!
</details>

<details closed>
<summary>Contributor Graph</summary>
<br>
<p align="left">
   <a href="https://github.com{/ag7dev/maggibot/}graphs/contributors">
      <img src="https://contrib.rocks/image?repo=ag7dev/maggibot">
   </a>
</p>
</details>

---

## ðŸŽ— License

This project is protected under the [MIT License](https://choosealicense.com/licenses) License. For more details, refer to the [LICENSE](https://choosealicense.com/licenses/) file.

---

## ðŸ™Œ Acknowledgments

- List any resources, contributors, inspiration, etc. here.

---

