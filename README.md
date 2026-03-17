<p align="center">
  <img src="assets/airsstool_logo.png" alt="airsstool logo" width="100" style="vertical-align: middle;">
  <span style="font-size: 2.5em; font-weight: bold; vertical-align: middle; margin-left: 15px;">airsstool</span>
</p>

<p align="center">
  <strong>Give your AI agent the ability to efficiently browse the web and read RSS feeds.</strong>
</p>

<p align="center">
  A RSSHub CLI tool and MCP server that enables AI agents to discover and fetch RSS feeds from 1500+ websites - GitHub trending, YouTube channels, Reddit threads, news sites, and more.
</p>

## ✨ Features

- 🤖 **MCP Server**: Expose RSSHub capabilities as MCP tools for AI agents
- 💻 **CLI Tool**: Command-line interface for manual RSS feed management
- 📁 **Subscription Management**: Organize RSS feeds into subscription groups
- 📄 **Multiple Output Formats**: RSS, Atom, JSON, RSS3, or **Markdown** for AI agents to read easily
- 🔍 **Content Filtering**: Filter by title, description, author, category, time
- 📊 **RSSHub Routes Database**: Built-in database of 1500+ RSSHub routes

## 🚀 Quick Start

### 📋 Prerequisites

- Python 3.10+
- A running RSSHub instance

### 📦 Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/airsstool.git
cd airsstool

# Install dependencies
pip install httpx mcp

# (Recommended) Install as a package for global CLI access
pip install .
```

### ⚙️ Configuration

Set environment variables for your RSSHub instance:

```bash
export RSSHUB_URL="http://your-rsshub-instance:1200"
```

Default is `https://rsshub.app`.

### 🗄️ Initialize Database

After installation, initialize the database:

```bash
airsstool init
```

This creates the database at `~/.airsstool/airsstoolDB.db` (or `%USERPROFILE%\.airsstool\airsstoolDB.db` on Windows).

**Options:**
- `--db-path PATH` - Custom database location
- `--force` - Force recreate (deletes existing database)

```bash
# Custom database path
airsstool init --db-path /custom/path/airsstoolDB.db

# Force recreate
airsstool init --force
```

> **Note**: You can replace `routes_data/rsshub-routes.json` with your own RSSHub routes data before running `init`. The JSON format should match RSSHub's official routes documentation.

## 📖 Usage

### 💻 CLI Tool

After installing and initializing, you can use the `airsstool` command directly:

```bash
# Initialize database (first time only)
airsstool init

# List all RSS categories
airsstool list categories

# List websites (with optional filters)
airsstool list websites
airsstool list websites --category programming --page-size 10

# List routes for a website
airsstool list routes youtube

# Check route details
airsstool check youtube user

# Fetch RSS content
airsstool fetch /github/trending/daily/javascript/en
airsstool fetch /youtube/user/@MrBeast --limit 5
airsstool fetch /hackernews/best --format rss --limit 10
airsstool fetch /instagram/user/instagram --brief 100

# Subscription management
airsstool add-subscription --user alice --subscription tech_news
airsstool subscribe --user alice --subscription tech_news --path /github/trending/daily/any/en --description "GitHub Trending"
airsstool fetch --user alice --subscription tech_news
```

### 🔌 MCP Server

Run the MCP server:

```bash
airsstool-mcp
```

Or if using with Claude Code or other MCP clients, add to your MCP configuration:

```json
{
  "mcpServers": {
    "airsstool": {
      "command": "airsstool-mcp",
      "env": {
        "RSSHUB_URL": "http://your-rsshub-instance:1200"
      }
    }
  }
}
```

#### 🛠️ Available MCP Tools

| Tool | Description |
|------|-------------|
| `list_rss_categories` | List all RSS categories |
| `list_rss_websites` | List websites with pagination and filtering |
| `list_rss_routes` | List routes for a website (fuzzy search supported) |
| `check_rss_route_detail` | Get detailed info about a route |
| `fetch_rss` | Fetch and parse RSS content |
| `list_users` | List all users |
| `list_rss_subscription` | List user's subscription groups |
| `list_rss_subscribed_paths` | List paths in a subscription |
| `add_rss_subscription` | Create a new subscription group |
| `subscribe_rss_path` | Add a path to subscription |
| `fetch_rss_subscription` | Fetch all paths in a subscription |

## 📚 CLI Commands Reference

### 📋 List Commands

```bash
airsstool list categories                          # List all categories
airsstool list websites [--category CAT] [--page-size N] [--page-num N]
airsstool list routes <website>                    # List routes for a website
airsstool list subscriptions --user USER           # List user's subscriptions
airsstool list paths --user USER --subscription NAME
airsstool list users                               # List all users
```

### 📥 Fetch Commands

```bash
airsstool fetch <path> [options]
airsstool fetch --user USER --subscription NAME [options]

Options:
  --limit N              Limit number of feeds
  --offset N             Skip first N feeds
  --format FORMAT        Output format: rss, atom, json, rss3
  --brief N              Output brief text (>=100 chars)
  --filter PATTERN       Filter title and description
  --filter-title PATTERN Filter title only
  --filter-time SECONDS  Filter by time range
  --filterout PATTERN    Exclude matching content
```

### 📰 Subscription Commands

```bash
airsstool add-subscription --user USER --subscription NAME
airsstool subscribe --user USER --subscription NAME --path PATH --description DESC [--force]
```

## 🔧 Custom Routes Data

Replace `routes_data/rsshub-routes.json` with your own data:

1. Get routes data from RSSHub's official repository
2. Or generate from your own RSSHub instance
3. Run `python process_rsshub_data.py` to rebuild the database

The `routes_data/rsshub_routes_with_heat_badges.html` file is a div section copied from [RSSHub's website HTML](https://docs.rsshub.app/routes/) to add heat information to websites.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

This project is built on top of **RSSHub**, an amazing open-source RSS hub.

- **RSSHub Code**: [https://github.com/DIYgod/RSSHub](https://github.com/DIYgod/RSSHub)
- **RSSHub Docs**: [https://docs.rsshub.app/](https://docs.rsshub.app/)

If you find airsstool useful, please consider starring both this project and RSSHub!