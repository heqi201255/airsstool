import sqlite3
import os
import math
import re
import html
import logging
import httpx
import xml.etree.ElementTree as ET
from difflib import get_close_matches
from typing import Optional
from urllib.parse import urlencode
from mcp.server.fastmcp import FastMCP

# 抑制 httpx 的 HTTP 请求日志（只显示警告和错误）
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_display_width(s: str) -> int:
    """计算字符串的显示宽度（中文字符算2，英文算1）"""
    width = 0
    for char in s:
        if '\u4e00' <= char <= '\u9fff':  # 中文字符范围
            width += 2
        else:
            width += 1
    return width


def pad_to_width(s: str, width: int, align: str = 'left') -> str:
    """将字符串填充到指定显示宽度"""
    current_width = get_display_width(s)
    padding = width - current_width
    if padding <= 0:
        return s
    if align == 'right':
        return ' ' * padding + s
    else:  # left
        return s + ' ' * padding

# 全局配置
RSSHUB_URL = os.environ.get("RSSHUB_URL", "https://rsshub.app")
RSSHUB_DOMAIN = RSSHUB_URL.lstrip("https://").lstrip("http://")


def get_default_db_path():
    """获取默认数据库路径，跨平台支持"""
    # 优先使用环境变量
    env_db_path = os.environ.get('AIRSSTOOL_DB_PATH')
    if env_db_path:
        return env_db_path

    # 默认使用用户目录下的 .airsstool 文件夹（隐藏目录）
    home_dir = os.path.expanduser('~')
    return os.path.join(home_dir, '.airsstool', 'airsstoolDB.db')


# 数据库路径
DB_PATH = get_default_db_path()

# 创建 MCP Server
mcp = FastMCP("RSSHub MCP Server")


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@mcp.tool()
def list_rss_categories() -> str:
    """获取全部RSS分类"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT category FROM Category
        WHERE category != 'Unspecified'
        ORDER BY category
    ''')

    categories = [row['category'] for row in cursor.fetchall()]
    conn.close()

    return '\n'.join(categories)


@mcp.tool()
def list_rss_websites(
    category: Optional[str] = None,
    page_size: int = 20,
    page_num: int = 1,
    enable_nsfw: bool = False
) -> str:
    """
    获取网站信息列表，可按分类筛选，按热度排序，支持分页。

    Args:
        category: 分类名称，为None时获取全部网站
        page_size: 每页数量，默认20
        page_num: 页码（从1开始），默认1
        enable_nsfw: 是否包含NSFW网站，默认False
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 验证分类是否有效
    if category:
        cursor.execute('SELECT id FROM Category WHERE category = ?', (category,))
        if not cursor.fetchone():
            conn.close()
            return f"'{category}' is not a valid category. Use 'airsstool list categories' to see all available categories."

    # 构建NSFW过滤条件
    nsfw_filter = "" if enable_nsfw else "WHERE nsfw = 0"

    # 获取总数
    if category:
        cursor.execute(f'''
            SELECT COUNT(DISTINCT w.id)
            FROM Website w
            JOIN WebsiteCategory wc ON w.id = wc.website_id
            JOIN Category c ON wc.category_id = c.id
            WHERE c.category = ? {'AND w.nsfw = 0' if not enable_nsfw else ''}
        ''', (category,))
    else:
        cursor.execute(f'SELECT COUNT(*) FROM Website {nsfw_filter}')

    total_count = cursor.fetchone()[0]
    # 确保 page_size 有效
    if page_size <= 0:
        page_size = 20

    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

    # 确保 page_num 在有效范围内
    page_num = max(1, min(page_num, total_pages))
    offset = (page_num - 1) * page_size

    if category:
        # 按分类查询
        cursor.execute(f'''
            SELECT DISTINCT w.name, w.url, w.lang, w.heat
            FROM Website w
            JOIN WebsiteCategory wc ON w.id = wc.website_id
            JOIN Category c ON wc.category_id = c.id
            WHERE c.category = ? {'AND w.nsfw = 0' if not enable_nsfw else ''}
            ORDER BY w.heat DESC
            LIMIT ? OFFSET ?
        ''', (category, page_size, offset))
    else:
        # 获取全部网站
        cursor.execute(f'''
            SELECT name, url, lang, heat
            FROM Website
            {nsfw_filter}
            ORDER BY heat DESC
            LIMIT ? OFFSET ?
        ''', (page_size, offset))

    websites = cursor.fetchall()
    conn.close()

    # 构建返回字符串
    category_label = "all" if category is None else category
    lines = [f"Result of category '{category_label}':", ""]

    # 表头 - 使用固定宽度
    col_name_width = 30
    col_url_width = 30
    col_lang_width = 8
    col_heat_width = 12

    header = f"    | {pad_to_width('Website Name', col_name_width)} | {pad_to_width('Website URL', col_url_width)} | {pad_to_width('Lang', col_lang_width)} | {pad_to_width('Heat', col_heat_width, 'right')} |"
    lines.append(header)
    lines.append("    " + "-" * (len(header) - 4))

    for w in websites:
        name = (w['name'] or '')[:28]
        url = (w['url'] or 'N/A')[:28]
        lang = (w['lang'] or 'N/A')[:6]
        heat = f"{w['heat']:,}" if w['heat'] else '0'
        lines.append(f"    | {pad_to_width(name, col_name_width)} | {pad_to_width(url, col_url_width)} | {pad_to_width(lang, col_lang_width)} | {pad_to_width(heat, col_heat_width, 'right')} |")

    lines.append("")
    lines.append("    Note: The 'Website URL' is not the RSS URL, you need to fetch the RSS routes of the website to get the actual RSS path.")
    lines.append("")
    lines.append(f"Page {page_num}/{total_pages}    Total: {total_count}    Page Size: {page_size}")

    return '\n'.join(lines)


@mcp.tool()
def list_rss_routes(website_name: str) -> str:
    """
    获取指定网站的所有RSS路由。支持模糊搜索，如果精确匹配失败会尝试模糊匹配。

    Args:
        website_name: 网站名称（不区分大小写）
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 先尝试精确匹配（不区分大小写）
    cursor.execute('''
        SELECT id, name FROM Website
        WHERE LOWER(name) = LOWER(?)
    ''', (website_name,))

    website = cursor.fetchone()

    if not website:
        # 模糊搜索：获取所有网站名称，按热度排序
        cursor.execute('''
            SELECT name FROM Website
            ORDER BY heat DESC
        ''')
        all_names = [row['name'] for row in cursor.fetchall()]

        # 使用 difflib 进行模糊匹配
        matches = get_close_matches(website_name, all_names, n=10, cutoff=0.3)

        conn.close()

        if matches:
            if len(matches) == 1:
                return f"There's no result for '{website_name}'. Did you mean '{matches[0]}'?"
            else:
                matches_str = ', '.join(f"'{m}'" for m in matches)
                return f"There's no result for '{website_name}'. Did you mean one of: {matches_str}?"
        else:
            return f"There's no result for '{website_name}'."

    website_id = website['id']
    actual_name = website['name']

    # 获取该网站的所有路由
    cursor.execute('''
        SELECT name FROM Route
        WHERE website_id = ?
        ORDER BY name
    ''', (website_id,))

    routes = [row['name'] for row in cursor.fetchall()]
    conn.close()

    if not routes:
        return f"No routes found for website '{actual_name}'."

    return f"Routes for '{actual_name}' ({len(routes)} total):\n" + '\n'.join(f"  - {r}" for r in routes)


@mcp.tool()
def check_rss_route_detail(website_name: str, route_name: str) -> str:
    """
    获取指定路由的详细信息。

    Args:
        website_name: 网站名称
        route_name: 路由名称
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 查找网站
    cursor.execute('''
        SELECT id, name FROM Website
        WHERE LOWER(name) = LOWER(?)
    ''', (website_name,))

    website = cursor.fetchone()

    if not website:
        conn.close()
        return f"Website '{website_name}' not found."

    website_id = website['id']
    actual_website_name = website['name']

    # 查找路由
    cursor.execute('''
        SELECT id, path, name, example, lang, description, url, requireConfig, nsfw
        FROM Route
        WHERE website_id = ? AND LOWER(name) = LOWER(?)
    ''', (website_id, route_name))

    route = cursor.fetchone()

    if not route:
        conn.close()
        return f"Route '{route_name}' not found for website '{actual_website_name}'."

    route_id = route['id']
    actual_route_name = route['name']

    # 构建返回信息
    lines = [f'Detailed info of the route "{actual_route_name}" of "{actual_website_name}":']

    # RSSHub Path
    if route['path']:
        lines.append(f"    RSSHub Path: {route['path']}")

    # Example
    if route['example']:
        example = route['example']
        example = example.replace("https://rsshub.app", RSSHUB_URL)
        example = example.replace("rsshub.app", RSSHUB_DOMAIN)
        lines.append(f"    Example: {example}")

    # Language
    if route['lang']:
        lines.append(f"    Language: {route['lang']}")

    # Description
    if route['description']:
        desc = route['description']
        desc = desc.replace("https://rsshub.app", RSSHUB_URL)
        desc = desc.replace("rsshub.app", RSSHUB_DOMAIN)
        lines.append(f"    Description: {desc}")

    # Parameters
    cursor.execute('''
        SELECT id, name, description, default_value, has_options
        FROM RouteParameter
        WHERE route_id = ?
        ORDER BY id
    ''', (route_id,))

    parameters = cursor.fetchall()

    if parameters:
        lines.append("    Parameters:")
        for param in parameters:
            param_id = param['id']
            param_name = param['name'] or 'N/A'
            param_desc = param['description'] or ''
            param_default = param['default_value']
            has_options = param['has_options']

            if not has_options:
                lines.append(f"        - {param_name}: {param_desc}")
            else:
                lines.append(f"        - {param_name}:")
                if param_default:
                    lines.append(f"            -- default: {param_default}")

                # 获取参数选项
                cursor.execute('''
                    SELECT label, value FROM RouteParameterOption
                    WHERE parameter_id = ?
                    ORDER BY id
                ''', (param_id,))

                options = cursor.fetchall()
                for opt in options:
                    lines.append(f"            -- {opt['value']} ({opt['label']})")

    # RequireConfig
    if route['requireConfig']:
        cursor.execute('''
            SELECT name, optional, description
            FROM RouteConfig
            WHERE route_id = ?
            ORDER BY id
        ''', (route_id,))

        configs = cursor.fetchall()

        if configs:
            lines.append("    RequireConfig:")
            for cfg in configs:
                optional_str = "(optional) " if cfg['optional'] else ""
                cfg_name = cfg['name'] or 'N/A'
                cfg_desc = cfg['description'] or ''
                cfg_line = f"{optional_str}{cfg_name}"
                if cfg_desc: cfg_line = f"{cfg_line}: {cfg_desc}"
                lines.append(f"        - {cfg_line}")

    # Original URL
    if route['url']:
        lines.append(f"    OriginalURL: {route['url']}")

    # NSFW Warning
    if route['nsfw']:
        lines.append("    Warning: This is a NSFW route.")

    conn.close()

    return '\n'.join(lines)


@mcp.tool()
def fetch_rss(
    rss_path: str,
    limit: int = 0,
    offset: int = 0,
    # 过滤参数
    filter: Optional[str] = None,
    filter_title: Optional[str] = None,
    filter_description: Optional[str] = None,
    filter_author: Optional[str] = None,
    filter_category: Optional[str] = None,
    filter_time: Optional[int] = None,
    filterout: Optional[str] = None,
    filterout_title: Optional[str] = None,
    filterout_description: Optional[str] = None,
    filterout_author: Optional[str] = None,
    filterout_category: Optional[str] = None,
    filter_case_sensitive: Optional[bool] = None,
    # 输出参数
    format: Optional[str] = None,  # markdown (default), rss, atom, json, rss3
    brief: Optional[int] = None,
) -> str:
    """
    获取并解析RSS内容，返回格式化的Markdown文本或原始格式。

    Args:
        rss_path: RSS路径，会自动与RSSHUB_URL拼接
        limit: 限制返回的feed数量，0表示全部。当format指定时，此参数会添加到URL中
        offset: 跳过前N个feed（仅format为markdown时有效）

        # 过滤参数（添加到URL query中）
        filter: 过滤标题和描述
        filter_title: 过滤标题
        filter_description: 过滤描述
        filter_author: 过滤作者
        filter_category: 过滤分类
        filter_time: 过滤时间，单位秒，返回指定时间范围内的内容
        filterout: 排除标题和描述中的内容
        filterout_title: 排除标题中的内容
        filterout_description: 排除描述中的内容
        filterout_author: 排除作者
        filterout_category: 排除分类
        filter_case_sensitive: 过滤是否区分大小写，默认True

        # 输出参数
        format: 输出格式，可选值: markdown (默认), rss, atom, json, rss3。默认返回Markdown格式
        brief: 输出简讯，指定字数(>=100)
    """
    # 构建URL query参数
    query_params = {}

    # 添加过滤参数
    if filter is not None:
        query_params['filter'] = filter
    if filter_title is not None:
        query_params['filter_title'] = filter_title
    if filter_description is not None:
        query_params['filter_description'] = filter_description
    if filter_author is not None:
        query_params['filter_author'] = filter_author
    if filter_category is not None:
        query_params['filter_category'] = filter_category
    if filter_time is not None:
        query_params['filter_time'] = filter_time
    if filterout is not None:
        query_params['filterout'] = filterout
    if filterout_title is not None:
        query_params['filterout_title'] = filterout_title
    if filterout_description is not None:
        query_params['filterout_description'] = filterout_description
    if filterout_author is not None:
        query_params['filterout_author'] = filterout_author
    if filterout_category is not None:
        query_params['filterout_category'] = filterout_category
    if filter_case_sensitive is not None:
        query_params['filter_case_sensitive'] = str(filter_case_sensitive).lower()

    # 添加输出参数
    # format 为 None 或 "markdown" 时，不添加到 URL 参数，返回解析后的 Markdown
    if format is not None and format != 'markdown':
        # 当指定非markdown格式时，limit作为URL参数，不支持offset
        if offset > 0:
            return f"'{format}' format does not support offset parameter."
        if limit > 0:
            query_params['limit'] = limit
        query_params['format'] = format
    if brief is not None:
        if brief < 100:
            return "brief parameter must be >= 100."
        query_params['brief'] = brief

    # 拼接完整URL
    if rss_path.startswith('http://') or rss_path.startswith('https://'):
        url = rss_path
    else:
        # 确保路径以/开头
        if not rss_path.startswith('/'):
            rss_path = '/' + rss_path
        url = RSSHUB_URL.rstrip('/') + rss_path

    # 添加query参数
    if query_params:
        url = url + ('&' if '?' in url else '?') + urlencode(query_params)

    try:
        # 获取RSS内容 - 添加请求头模拟浏览器行为
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml, application/json, */*',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        }
        # trust_env=False 禁用环境代理，避免代理导致的 502 错误
        with httpx.Client(timeout=30.0, follow_redirects=True, trust_env=False) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            content = response.text
    except httpx.HTTPError as e:
        return f"Error fetching RSS: {str(e)}"

    # 如果指定了非markdown格式或brief，直接返回原始内容
    if (format is not None and format != 'markdown') or brief is not None:
        return content

    # 解析XML并转换为Markdown
    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        return f"Error parsing XML: {str(e)}"

    # 解析channel信息
    channel = root.find('channel')
    if channel is None:
        return "Error: No channel found in RSS feed"

    # 获取feed标题和链接
    feed_title = channel.findtext('title', 'Unknown Feed')
    feed_link = channel.findtext('link', '')
    feed_description = channel.findtext('description', '')

    # 构建Markdown输出
    lines = [f"# {feed_title}"]
    if feed_link:
        lines.append(f"\n**Feed URL:** {url}")
    if feed_description:
        lines.append(f"\n**Description:** {feed_description.strip()}")
    lines.append("\n---\n")

    # 获取所有items
    all_items = channel.findall('item')
    total = len(all_items)

    # 应用offset和limit（仅在markdown模式下）
    start_idx = min(offset, total)
    if limit > 0:
        end_idx = min(start_idx + limit, total)
    else:
        end_idx = total

    items = all_items[start_idx:end_idx]

    # 解析items
    for i, item in enumerate(items, start_idx + 1):
        title = item.findtext('title', 'No Title')
        link = item.findtext('link', '')
        pub_date = item.findtext('pubDate', '')
        author = item.findtext('author', '')
        description = item.findtext('description', '')

        # 添加标题
        lines.append(f"## {i}. {title}")

        # 添加元数据
        meta_parts = []
        if author:
            meta_parts.append(f"**Author:** {author}")
        if pub_date:
            meta_parts.append(f"**Date:** {pub_date}")
        if meta_parts:
            lines.append(" | ".join(meta_parts))

        # 添加链接
        if link:
            lines.append(f"**Link:** {link}")

        # 处理description - 提取文字和链接
        if description:
            # HTML实体解码
            description = html.unescape(description)

            # 提取图片链接
            img_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
            images = re.findall(img_pattern, description)

            # 提取iframe/视频链接
            iframe_pattern = r'<iframe[^>]+src=["\']([^"\']+)["\']'
            iframes = re.findall(iframe_pattern, description)

            # 提取普通链接
            link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
            links = re.findall(link_pattern, description)

            # 移除HTML标签，保留文字
            text = re.sub(r'<br\s*/?>', '\n', description)
            text = re.sub(r'</p>', '\n', text)
            text = re.sub(r'<[^>]+>', '', text)
            text = html.unescape(text)
            text = re.sub(r'\n\s*\n', '\n\n', text)
            text = text.strip()

            # 添加描述文字
            if text:
                lines.append(f"\n{text}")

            # 添加图片链接
            if images:
                lines.append("\n**Images:**")
                for img_url in images[:3]:  # 最多显示3张图片
                    lines.append(f"- ![]({img_url})")

            # 添加视频链接
            if iframes:
                lines.append("\n**Videos:**")
                for iframe_url in iframes[:2]:  # 最多显示2个视频
                    lines.append(f"- [Video]({iframe_url})")

            # 添加相关链接
            if links:
                lines.append("\n**Links:**")
                for link_url, link_text in links[:5]:  # 最多显示5个链接
                    lines.append(f"- [{link_text}]({link_url})")

        # 添加enclosure（如封面图）
        enclosure = item.find('enclosure')
        if enclosure is not None:
            enclosure_url = enclosure.get('url', '')
            enclosure_type = enclosure.get('type', '')
            if enclosure_url and enclosure_type.startswith('image'):
                lines.append(f"\n**Thumbnail:** ![]({enclosure_url})")

        lines.append("\n---\n")

    # 添加浏览信息
    if total > 0:
        lines.append(f"Viewing {start_idx + 1}-{end_idx} of {total} feeds.")

    return '\n'.join(lines)


@mcp.tool()
def list_users() -> str:
    """获取所有用户列表"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT DISTINCT user FROM UserSubscription ORDER BY user')
    users = [row['user'] for row in cursor.fetchall()]
    conn.close()

    if not users:
        return "No users found."

    lines = ["Users:"]
    for user in users:
        lines.append(f"    {user}")

    return '\n'.join(lines)


@mcp.tool()
def list_rss_subscription(user: str) -> str:
    """
    获取用户的所有订阅组。

    Args:
        user: 用户名称（AI agent 则使用 agent 自己的名字）
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT subscription_name, route_count
        FROM UserSubscription
        WHERE user = ?
        ORDER BY subscription_name
    ''', (user,))

    subscriptions = cursor.fetchall()
    conn.close()

    if not subscriptions:
        return f"No subscriptions found for user '{user}'."

    lines = [f"User: {user}    Total Subscriptions: {len(subscriptions)}"]
    lines.append("| Name | Total Subscribed Feeds |")
    lines.append("|------|------------------------|")

    for sub in subscriptions:
        lines.append(f"| {sub['subscription_name']} | {sub['route_count']} |")

    return '\n'.join(lines)


@mcp.tool()
def list_rss_subscribed_paths(user: str, subscription_name: str) -> str:
    """
    获取用户订阅组中的所有路径。

    Args:
        user: 用户名称
        subscription_name: 订阅组名称
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 查找 subscription_id
    cursor.execute('''
        SELECT id FROM UserSubscription
        WHERE user = ? AND subscription_name = ?
    ''', (user, subscription_name))

    result = cursor.fetchone()
    if not result:
        conn.close()
        return f"Subscription '{subscription_name}' not found for user '{user}'."

    subscription_id = result['id']

    # 获取所有路径
    cursor.execute('''
        SELECT description, path
        FROM SubscribedPath
        WHERE subscription_id = ?
        ORDER BY id
    ''', (subscription_id,))

    paths = cursor.fetchall()
    conn.close()

    if not paths:
        return f"No paths found in subscription '{subscription_name}'."

    lines = [f"User: {user}    Subscription: {subscription_name}"]
    lines.append("| Description | RSS Path |")
    lines.append("|-------------|----------|")

    for p in paths:
        desc = p['description'] or 'N/A'
        lines.append(f"| {desc} | {p['path']} |")

    return '\n'.join(lines)


@mcp.tool()
def add_rss_subscription(user: str, subscription_name: str) -> str:
    """
    为用户新增一个订阅组。

    Args:
        user: 用户名称
        subscription_name: 订阅组名称
    """
    # 验证参数
    if not user or not user.strip():
        return "Error: user name cannot be empty."
    if not subscription_name or not subscription_name.strip():
        return "Error: subscription name cannot be empty."

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO UserSubscription (user, subscription_name, route_count)
            VALUES (?, ?, 0)
        ''', (user, subscription_name))
        conn.commit()
        conn.close()
        return f"Successfully added subscription '{subscription_name}' to user '{user}'."
    except sqlite3.IntegrityError:
        conn.close()
        return f"Subscription '{subscription_name}' already exists for user '{user}'."


@mcp.tool()
def subscribe_rss_path(user: str, subscription_name: str, path_description: str, path: str, force: bool = False) -> str:
    """
    为用户的订阅组添加路径。

    Args:
        user: 用户名称
        subscription_name: 订阅组名称
        path_description: 路径描述
        path: RSS路径（不能是完整URL）
        force: 是否强制添加（跳过连通性检查）
    """
    # 验证参数
    if not user or not user.strip():
        return "Error: user name cannot be empty."
    if not subscription_name or not subscription_name.strip():
        return "Error: subscription name cannot be empty."
    if not path or not path.strip():
        return "Error: path cannot be empty."

    # 检查 path 是否是完整 URL (任何包含 :// 的都视为完整 URL)
    if '://' in path:
        return "Please add the route path (e.g., /github/trending/daily/any/en), not the full URL."

    # 确保 path 以 / 开头
    if not path.startswith('/'):
        path = '/' + path

    # 验证路径连通性（除非强制添加）
    if not force:
        test_result = fetch_rss(path, limit=1)
        if test_result.startswith("Error fetching RSS:"):
            return f"This path cannot be fetched currently, possibly due to network issues or the path is invalid. Unable to add. Use force=True to add anyway."

    conn = get_db_connection()
    cursor = conn.cursor()

    # 查找 subscription_id
    cursor.execute('''
        SELECT id FROM UserSubscription
        WHERE user = ? AND subscription_name = ?
    ''', (user, subscription_name))

    result = cursor.fetchone()
    if not result:
        conn.close()
        return f"Subscription '{subscription_name}' not found for user '{user}'. Please create it first."

    subscription_id = result['id']

    # 添加路径
    cursor.execute('''
        INSERT INTO SubscribedPath (subscription_id, description, path)
        VALUES (?, ?, ?)
    ''', (subscription_id, path_description, path))

    # 更新 route_count
    cursor.execute('''
        UPDATE UserSubscription
        SET route_count = route_count + 1
        WHERE id = ?
    ''', (subscription_id,))

    conn.commit()
    conn.close()

    return f"Successfully added path to subscription '{subscription_name}'."


@mcp.tool()
def fetch_rss_subscription(
    user: str,
    subscription_name: str,
    limit: int = 0,
    offset: int = 0,
    # 过滤参数
    filter: Optional[str] = None,
    filter_title: Optional[str] = None,
    filter_description: Optional[str] = None,
    filter_author: Optional[str] = None,
    filter_category: Optional[str] = None,
    filter_time: Optional[int] = None,
    filterout: Optional[str] = None,
    filterout_title: Optional[str] = None,
    filterout_description: Optional[str] = None,
    filterout_author: Optional[str] = None,
    filterout_category: Optional[str] = None,
    filter_case_sensitive: Optional[bool] = None,
    # 输出参数
    format: Optional[str] = None,  # markdown (default), rss, atom, json, rss3
    brief: Optional[int] = None,
) -> str:
    """
    获取用户订阅组中所有路径的 RSS 内容。

    Args:
        user: 用户名称
        subscription_name: 订阅组名称
        limit: 限制每个路径返回的feed数量，0表示全部
        offset: 每个路径跳过前N个feed（仅format为markdown时有效）

        # 过滤参数（传递给fetch_rss）
        filter: 过滤标题和描述
        filter_title: 过滤标题
        filter_description: 过滤描述
        filter_author: 过滤作者
        filter_category: 过滤分类
        filter_time: 过滤时间，单位秒
        filterout: 排除标题和描述中的内容
        filterout_title: 排除标题中的内容
        filterout_description: 排除描述中的内容
        filterout_author: 排除作者
        filterout_category: 排除分类
        filter_case_sensitive: 过滤是否区分大小写

        # 输出参数
        format: 输出格式，可选值: markdown (默认), rss, atom, json, rss3。默认返回Markdown格式
        brief: 输出简讯字数(>=100)
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 查找 subscription_id
    cursor.execute('''
        SELECT id FROM UserSubscription
        WHERE user = ? AND subscription_name = ?
    ''', (user, subscription_name))

    result = cursor.fetchone()
    if not result:
        conn.close()
        return f"Subscription '{subscription_name}' not found for user '{user}'. Please create a subscription first."

    subscription_id = result['id']

    # 获取所有路径
    cursor.execute('''
        SELECT description, path
        FROM SubscribedPath
        WHERE subscription_id = ?
        ORDER BY id
    ''', (subscription_id,))

    paths = cursor.fetchall()
    conn.close()

    if not paths:
        return f"No paths found in subscription '{subscription_name}'."

    # 获取每个路径的 RSS 内容，记录成功和失败
    results = []
    failed_paths = []

    for p in paths:
        desc = p['description'] or p['path']
        path = p['path']
        try:
            rss_content = fetch_rss(
                path,
                limit=limit,
                offset=offset,
                filter=filter,
                filter_title=filter_title,
                filter_description=filter_description,
                filter_author=filter_author,
                filter_category=filter_category,
                filter_time=filter_time,
                filterout=filterout,
                filterout_title=filterout_title,
                filterout_description=filterout_description,
                filterout_author=filterout_author,
                filterout_category=filterout_category,
                filter_case_sensitive=filter_case_sensitive,
                format=format,
                brief=brief,
            )
            # 检查是否是错误响应
            if rss_content.startswith("Error fetching RSS:") or rss_content.startswith("Error parsing XML:"):
                failed_paths.append(f"{desc} ({path}): {rss_content}")
            elif rss_content.endswith("does not support offset parameter."):
                return rss_content  # 直接返回错误信息
            else:
                results.append(f"=== {desc} ===\n{rss_content}")
        except Exception as e:
            failed_paths.append(f"{desc} ({path}): Unexpected error - {str(e)}")

    # 构建最终结果
    output_parts = []

    if results:
        output_parts.append('\n\n'.join(results))

    if failed_paths:
        failure_report = "=== Failed Sources ===\n" + '\n'.join(f"- {fp}" for fp in failed_paths)
        output_parts.append(failure_report)

    if not results and not failed_paths:
        return "No content retrieved."

    return '\n\n'.join(output_parts)


def main():
    """Entry point for airsstool-mcp command"""
    mcp.run()


if __name__ == "__main__":
    main()