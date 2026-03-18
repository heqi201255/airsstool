<div align="center">
  <img src="assets/airsstool_logo.png" alt="airsstool logo" width="150">
  <h1>airsstool</h1>
  <p>Give your AI agent the ability to efficiently browse the web and fetch RSS feeds.</p>
  <p>Please give this repo a 🌟star if you find it helpful</p>
</div>

---

<p align="center">
  <i>A RSSHub CLI tool and MCP server that enables AI agents to discover and fetch RSS feeds from 1500+ websites - GitHub trending, YouTube channels, Reddit threads, news sites, and more.</i>
</p>

## ✨ Features

- 🤖 **MCP Server**: Expose RSSHub capabilities as MCP tools for AI agents
- 💻 **CLI Tool**: Command-line interface for manual RSS feed management
- 📁 **Subscription Management**: Organize RSS feeds into subscription groups
- 📃 **Multiple Output Formats**: **Markdown** (default, agent-friendly & token-efficient), plus all formats natively supported by RSSHub (RSS, Atom, JSON Feed, and RSS3)
- 🔍 **Content Filtering**: Leverage RSSHub's native filtering (title, description, author, category, time)
- 🔌 **RSSHub Routes Database**: Built-in database of 3000+ RSSHub routes

## ❓ Why airsstool?

### The RSS Advantage

While browser automation tools (like Playwright, Puppeteer) can render and extract content from any website, they come with overhead: launching a browser instance, waiting for page loads, and parsing complex HTML. For real-time content fetching, this can be overkill.

**RSS** (Really Simple Syndication) offers a lightweight alternative - it's a standardized format for distributing content, like a "news feed" that websites publish. RSSHub extends this to 1500+ websites that don't natively offer RSS, parsing and standardizing their content.

airsstool bridges RSSHub with AI agents by providing:

- **Lightweight & fast** - No browser needed, just HTTP requests to structured feeds
- **Token-efficient Markdown** - Clean, structured output by default (vs verbose HTML)
- **One consistent API** - Same interface for YouTube, GitHub, Instagram, news sites, etc.
- **Built-in filtering** - Leverage RSSHub's native filtering by keywords, time, authors
- **Reliable structure** - RSS feeds have consistent schema, no need for site-specific parsers

### When to Use airsstool

| Use Case | Example Questions | Works? |
|----------|-------------------|--------|
| **Real-time news tracking** | "What's the latest on the election?"<br>"Any updates on the earthquake?" | ✅ Perfect for live events |
| **Content monitoring** | "Any new posts from MrBeast?"<br>"Show me today's GitHub trending" | ✅ Ideal for scheduled checks |
| **Topic filtering** | "Find AI news from Hacker News"<br>"Bitcoin price updates" | ✅ Great with filters |
| **Multi-source aggregation** | "Get updates from all my subscriptions" | ✅ Built for this |
| **Historical research** | "What happened in 2020?"<br>"Compare news from last year" | ❌ Use web search instead |
| **Deep content analysis** | "Summarize this specific article"<br>"Extract data from this page" | ❌ Use browser tools instead |
| **Interactive websites** | "Book a flight"<br>"Fill out this form" | ❌ Not designed for this |


## 🚀 Quick Start

### 📋 Prerequisites

- Python 3.10+
- A running RSSHub instance

### 📦 Installation

```bash
# Clone the repository
git clone https://github.com/heqi201255/airsstool.git
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

This will automatically download routes data from your RSSHub instance (`$RSSHUB_URL/api/namespace`) and create the database at `~/.airsstool/airsstoolDB.db` (or `%USERPROFILE%\.airsstool\airsstoolDB.db` on Windows).

**Options:**
- `--db-path PATH` - Custom database location
- `--force` - Force recreate (deletes existing database)

```bash
# Custom database path
airsstool init --db-path /custom/path/airsstoolDB.db

# Force recreate
airsstool init --force
```

> **Note**: Routes data is automatically downloaded from your RSSHub instance during `init`. If the download fails, you can manually place a `rsshub-routes.json` file in `~/.airsstool/` before running `init`. The JSON format should match RSSHub's official routes documentation.

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
airsstool list websites [--category CAT] [--page-size N] [--page-num N] [--enable-nsfw]
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
  --format FORMAT        Output format: markdown (default), rss, atom, json, rss3
  --brief N              Output brief text (>=100 chars)
  --filter PATTERN       Filter title and description
  --filter-title PATTERN Filter title only
  --filter-time SECONDS  Filter by time range
  --filterout PATTERN    Exclude matching content
  --enable-nsfw          Include NSFW content (for list websites)
```

### 📰 Subscription Commands

```bash
airsstool add-subscription --user USER --subscription NAME
airsstool subscribe --user USER --subscription NAME --path PATH --description DESC [--force]
```

## 🤖 For OpenClaw Users

If you're using [OpenClaw](https://github.com/openclaw/openclaw), the `SKILL.md` file in this repository provides instructions for the OpenClaw agent to use airsstool. The agent will automatically read this file and learn how to:

- Install and configure airsstool
- Use CLI commands to discover and fetch RSS feeds
- Handle errors and troubleshooting

Simply point your OpenClaw configuration to this repository's SKILL.md file. The skill will be uploaded to ClawHub soon.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

This project is built on top of **RSSHub**, an amazing open-source RSS hub.

- **RSSHub Code**: [https://github.com/DIYgod/RSSHub](https://github.com/DIYgod/RSSHub)
- **RSSHub Docs**: [https://docs.rsshub.app/](https://docs.rsshub.app/)

If you find airsstool useful, please consider starring both this project and RSSHub!