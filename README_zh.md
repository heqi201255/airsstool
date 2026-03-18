<div align="center">
  <img src="assets/airsstool_logo.png" alt="airsstool logo" width="150">
  <h1>airsstool</h1>
  <p>让你的 AI Agent 高效获取网站内容和 RSS 订阅</p>
  <p>如果觉得有用，请给个 🌟star 支持一下</p>
</div>

---

<p align="center">
  <i>一个 RSSHub CLI 工具和 MCP 服务器，让 AI Agent 能够从 1500+ 网站获取内容 - GitHub 趋势、YouTube 频道、Reddit 帖子、新闻网站等。</i>
</p>

<p align="center">
  <a href="README.md">English</a>
</p>

## ✨ 特性

- 🤖 **MCP Server**: 将 RSSHub 能力暴露为 MCP 工具供 AI Agent 使用
- 💻 **CLI 工具**: 命令行界面，方便手动管理 RSS 订阅
- 📁 **订阅管理**: 将 RSS 订阅源组织成订阅组
- 📃 **多种输出格式**: **Markdown**（默认，对 Agent 友好且节省 token），以及 RSSHub 原生支持的所有格式（RSS、Atom、JSON Feed、RSS3）
- 🔍 **内容过滤**: 利用 RSSHub 原生过滤能力（标题、描述、作者、分类、时间）
- 🔌 **RSSHub 路由数据库**: 内置 3000+ RSSHub 路由数据库

## ❓ 为什么选择 airsstool？

### RSS 的优势

虽然浏览器自动化工具（如 Playwright、Puppeteer）可以渲染和提取任何网站的内容，但它们有开销：启动浏览器实例、等待页面加载、解析复杂的 HTML。对于实时内容获取来说，这可能有些"杀鸡用牛刀"。

**RSS**（Really Simple Syndication）提供了一种轻量级的替代方案 - 它是一种标准化的内容分发格式，就像网站发布的"新闻源"。RSSHub 将这种能力扩展到了 1500+ 本身不提供 RSS 的网站，解析并标准化它们的内容。

airsstool 通过以下方式将 RSSHub 与 AI Agent 连接：

- **轻量快速** - 无需浏览器，只需 HTTP 请求获取结构化的订阅源
- **节省 Token 的 Markdown** - 默认输出干净、结构化的内容（对比冗长的 HTML）
- **统一的 API** - YouTube、GitHub、Instagram、新闻网站等使用相同的接口
- **内置过滤** - 利用 RSSHub 原生过滤能力，按关键词、时间、作者筛选
- **可靠的结构** - RSS 订阅源有一致的结构，无需为每个网站编写解析器

### 适用场景

| 场景 | 示例问题 | 适用？ |
|------|----------|--------|
| **实时新闻追踪** | "选举最新消息是什么？"<br>"地震有什么更新吗？" | ✅ 非常适合实时事件 |
| **内容监控** | "MrBeast 有新视频吗？"<br>"看看今天的 GitHub 趋势" | ✅ 适合定期检查 |
| **主题过滤** | "从 Hacker News 找 AI 新闻"<br>"比特币价格更新" | ✅ 配合过滤功能很好用 |
| **多源聚合** | "获取我所有订阅的更新" | ✅ 专门为此设计 |
| **历史研究** | "2020 年发生了什么？"<br>"对比去年的新闻" | ❌ 请使用网页搜索 |
| **深度内容分析** | "总结这篇特定文章"<br>"从这个页面提取数据" | ❌ 请使用浏览器工具 |
| **交互式网站** | "预订机票"<br>"填写表单" | ❌ 不适用于此场景 |


## 🚀 快速开始

### 📋 前置条件

- Python 3.10+
- 一个运行中的 RSSHub 实例

### 📦 安装

```bash
pip install airsstool
```

如果你使用 macOS 并安装了 Homebrew，推荐通过 pipx 安装（更容易让 Agent 找到命令）：

```bash
brew install pipx
pipx install airsstool
```

### ⚙️ 配置

设置 RSSHub 实例的环境变量：

```bash
export RSSHUB_URL="http://your-rsshub-instance:1200"
```

默认使用 `https://rsshub.app`。

### 🗄️ 初始化数据库

安装后，初始化数据库：

```bash
airsstool init
```

这会自动从你的 RSSHub 实例（`$RSSHUB_URL/api/namespace`）下载路由数据，并在 `~/.airsstool/airsstoolDB.db`（Windows 为 `%USERPROFILE%\.airsstool\airsstoolDB.db`）创建数据库。

**选项：**
- `--db-path PATH` - 自定义数据库位置
- `--force` - 强制重建（删除现有数据库）

```bash
# 自定义数据库路径
airsstool init --db-path /custom/path/airsstoolDB.db

# 强制重建
airsstool init --force
```

> **注意**：路由数据会在 `init` 时自动从 RSSHub 实例下载。如果下载失败，可以手动将 `rsshub-routes.json` 文件放到 `~/.airsstool/` 目录，然后再运行 `init`。JSON 格式应与 RSSHub 官方路由文档一致。

## 📖 使用方法

### 💻 CLI 工具

安装并初始化后，可以直接使用 `airsstool` 命令：

```bash
# 初始化数据库（首次使用）
airsstool init

# 列出所有分类
airsstool list categories

# 列出网站（可带过滤条件）
airsstool list websites
airsstool list websites --category programming --page-size 10

# 列出网站的路由
airsstool list routes youtube

# 查看路由详情
airsstool check youtube user

# 获取 RSS 内容
airsstool fetch /github/trending/daily/javascript/en
airsstool fetch /youtube/user/@MrBeast --limit 5
airsstool fetch /hackernews/best --format rss --limit 10
airsstool fetch /instagram/user/instagram --brief 100

# 订阅管理
airsstool add-subscription --user alice --subscription tech_news
airsstool subscribe --user alice --subscription tech_news --path /github/trending/daily/any/en --description "GitHub Trending"
airsstool fetch --user alice --subscription tech_news
```

### 🔌 MCP Server

运行 MCP 服务器：

```bash
airsstool-mcp
```

或者与 Claude Code 或其他 MCP 客户端配合使用，添加到 MCP 配置：

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

#### 🛠️ 可用的 MCP 工具

| 工具 | 描述 |
|------|------|
| `list_rss_categories` | 列出所有分类 |
| `list_rss_websites` | 列出网站（支持分页和过滤） |
| `list_rss_routes` | 列出网站的路由（支持模糊搜索） |
| `check_rss_route_detail` | 获取路由详细信息 |
| `fetch_rss` | 获取并解析 RSS 内容 |
| `list_users` | 列出所有用户 |
| `list_rss_subscription` | 列出用户的订阅组 |
| `list_rss_subscribed_paths` | 列出订阅组中的路径 |
| `add_rss_subscription` | 创建新的订阅组 |
| `subscribe_rss_path` | 添加路径到订阅组 |
| `unsubscribe_rss_subscription` | 删除订阅组及其所有路径 |
| `remove_rss_path` | 从订阅组中删除指定路径 |
| `fetch_rss_subscription` | 获取订阅组中所有路径的内容 |

## 📚 CLI 命令参考

### 📋 列表命令

```bash
airsstool list categories                          # 列出所有分类
airsstool list websites [--category CAT] [--page-size N] [--page-num N] [--enable-nsfw]
airsstool list routes <website>                    # 列出网站的路由
airsstool list subscriptions --user USER           # 列出用户的订阅组
airsstool list paths --user USER --subscription NAME
airsstool list users                               # 列出所有用户
```

### 📥 获取命令

```bash
airsstool fetch <path> [options]
airsstool fetch --user USER --subscription NAME [options]

Options:
  --limit N              限制返回数量
  --offset N             跳过前 N 条
  --format FORMAT        输出格式: markdown（默认）、rss、atom、json、rss3
  --brief N              输出简讯（>=100 字符）
  --filter PATTERN       过滤标题和描述
  --filter-title PATTERN 只过滤标题
  --filter-time SECONDS  按时间范围过滤
  --filterout PATTERN    排除匹配的内容
  --enable-nsfw          包含 NSFW 内容（用于 list websites）
```

### 📰 订阅命令

```bash
airsstool add-subscription --user USER --subscription NAME
airsstool subscribe --user USER --subscription NAME --path PATH --description DESC [--force]
airsstool unsubscribe --user USER --subscription NAME
airsstool remove-subscription --user USER --subscription NAME --path PATH
```

## 🤖 OpenClaw 用户

配套的 skill 已在 ClawHub 上发布，名称为 **Site Feeds**。安装方式：

```bash
clawhub install site-feeds
```

该 skill 让 OpenClaw Agent 能够使用 airsstool 获取网站更新和内容。

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

本项目基于 **RSSHub** 构建，感谢这个出色的开源 RSS 聚合项目。

- **RSSHub 代码**: [https://github.com/DIYgod/RSSHub](https://github.com/DIYgod/RSSHub)
- **RSSHub 文档**: [https://docs.rsshub.app/](https://docs.rsshub.app/)

如果你觉得 airsstool 有用，请同时给本项目和 RSSHub 点个 star！