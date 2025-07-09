<p align="center">
    <img src="https://img.icons8.com/external-tal-revivo-regular-tal-revivo/96/external-readme-is-a-easy-to-build-a-developer-hub-that-adapts-to-the-user-logo-regular-tal-revivo.png" align="center" width="30%">
</p>
<p align="center"><h1 align="center">MAGGIBOT</h1></p>
<p align="center">
	<em><code>❯ Made by AG7</code></em>
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

## 🔗 Table of Contents

- [📍 Overview](#-overview)
- [👾 Features](#-features)
- [📁 Project Structure](#-project-structure)
  - [📂 Project Index](#-project-index)
- [🚀 Getting Started](#-getting-started)
  - [☑️ Prerequisites](#-prerequisites)
  - [⚙️ Installation](#-installation)
  - [🤖 Usage](#🤖-usage)
  - [🧪 Testing](#🧪-testing)
- [📌 Project Roadmap](#-project-roadmap)
- [🔰 Contributing](#-contributing)
- [🎗 License](#-license)
- [🙌 Acknowledgments](#-acknowledgments)

---

## 📍 Overview

**Maggibot** is a modular Discord bot written in Python using
[`py-cord`](https://github.com/Pycord-Development/pycord). It is designed to be
extended through cogs and provides a wide range of moderation and community
management tools. The bot relies on a small set of configuration and data files
(see [`handlers/config.py`](handlers/config.py)) and can be customised via an
environment file based on `.env.example`.

---

## 👾 Features

- **Administration** – tools like autoroles, configuration commands and voice
  gate management.
- **Moderation** – classic moderation actions (kick, ban, mute) plus community
  voting utilities.
- **Protection** – modules for anti-spam, anti-raid, anti-ghost ping and webhook
  defence.
- **Statistics** – XP and leaderboard system with adjustable multipliers.
- **Ticket system** – simple ticket creation workflow for support channels.
- **Fun and utilities** – quotes, tags, TikTok downloader and more.

---

## 📁 Project Structure

```sh
└── maggibot/
    ├── README.md
    ├── assets
    │   └── All the Mp3 files are stored here
    ├── cogs
    │   └── All Cogs Are Stored here
    │       └── Including all Files
    ├── config
    │   └── All Config Files Are Stored here
    ├── data
    │   └── All data like stats ans so on are stored here
    ├── extensions
    │   └── All extensions are stored here
    ├── handlers
    │   └── All Handlers are here
    ├── main.py
    ├── requirements.txt
    └── start.bat
```


### 📂 Project Index
<details open>
	<summary><b><code>MAGGIBOT/</code></b></summary>
	<details> <!-- __root__ Submodule -->
		<summary><b>__root__</b></summary>
		<blockquote>
			<table>
			<tr>
				<td><b><a href='https://github.com/ag7dev/maggibot/blob/master/main.py'>main.py</a></b></td>
				<td><code>❯ Main entry point of the bot.</code></td>
			</tr>
			<tr>
				<td><b><a href='https://github.com/ag7dev/maggibot/blob/master/requirements.txt'>requirements.txt</a></b></td>
				<td><code>❯ Required packages for the bot.</code></td>
			</tr>
			<tr>
				<td><b><a href='https://github.com/ag7dev/maggibot/blob/master/start.bat'>start.bat</a></b></td>
				<td><code>❯ Bat file to start the bot.</code></td>
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
				<td><code>❯ Debug Handler</code></td>
			</tr>
			<tr>
				<td><b><a href='https://github.com/ag7dev/maggibot/blob/master/handlers/config.py'>config.py</a></b></td>
				<td><code>❯ Handler for config</code></td>
			</tr>
			<tr>
				<td><b><a href='https://github.com/ag7dev/maggibot/blob/master/handlers/env.py'>env.py</a></b></td>
				<td><code>❯ env handler</code></td>
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
				<td><code>❯ Voicegate config</code></td>
			</tr>
			<tr>
				<td><b><a href='https://github.com/ag7dev/maggibot/blob/master/config/serverconfig.json'>serverconfig.json</a></b></td>
				<td><code>❯ Serverconfig</code></td>
			</tr>
			<tr>
				<td><b><a href='https://github.com/ag7dev/maggibot/blob/master/config/lockdown.json'>lockdown.json</a></b></td>
				<td><code>❯ Lockdown config</code></td>
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
				<td><code>❯ Mod extensions</code></td>
			</tr>
			<tr>
				<td><b><a href='https://github.com/ag7dev/maggibot/blob/master/extensions/statsextension.py'>statsextension.py</a></b></td>
				<td><code>❯ Stats extension</code></td>
			</tr>
			</table>
		</blockquote>
	</details>
</details>

---
## 🚀 Getting Started

### ☑️ Prerequisites

Before getting started with maggibot, ensure your runtime environment meets the following requirements:

- **Programming Language:** Python
- **Package Manager:** Pip


### ⚙️ Installation

See [INSTALL.md](INSTALL.md) for a full step-by-step installation guide. In
clone the repository, create a virtual environment with `python -m venv venv`, activate it and install the dependencies with `pip install -r requirements.txt`, copy `.env.example` to `.env` and run `python main.py install` once to create the default configuration files.



### 🤖 Usage
Run Maggibot with the helper script:

Run `start.bat` on Windows or `python main.py` from an activated virtual environment.

---
## 📌 Project Roadmap

- [X] **`Task 1`**: <strike>Main Structure.</strike>
- [X] **`Task 2`**: <strike>Installer.</strike>
- [ ] **`Task 3`**: More Protection Features.

---

## 🔰 Contributing

- **💬 [Join the Discussions](https://github.com/ag7dev/maggibot/discussions)**: Share your insights, provide feedback, or ask questions.
- **🐛 [Report Issues](https://github.com/ag7dev/maggibot/issues)**: Submit bugs found or log feature requests for the `maggibot` project.
- **💡 [Submit Pull Requests](https://github.com/ag7dev/maggibot/blob/main/CONTRIBUTING.md)**: Review open PRs, and submit your own PRs.

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

## 🎗 License

This project is protected under the [MIT License](https://choosealicense.com/licenses) License. For more details, refer to the [LICENSE](https://choosealicense.com/licenses/) file.

---

## 🙌 Acknowledgments

- List any resources, contributors, inspiration, etc. here.

---
