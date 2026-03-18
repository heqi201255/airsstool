import json
import re
import sqlite3
from collections import defaultdict
import os
import httpx

# 文件路径
SCRIPT_DIR = os.path.dirname(__file__)
HEAT_DATA_DIR = os.path.join(SCRIPT_DIR, 'routes_heat_data')
HEAT_JSON_PATH = os.path.join(HEAT_DATA_DIR, 'rsshub-routes-heat.json')

# RSSHub URL (from environment or default)
RSSHUB_URL = os.environ.get("RSSHUB_URL", "https://rsshub.app")


def get_default_data_dir():
    """获取默认数据目录路径 (~/.airsstool)"""
    home_dir = os.path.expanduser('~')
    return os.path.join(home_dir, '.airsstool')


def get_routes_json_path():
    """获取routes JSON的路径 (在~/.airsstool目录下)"""
    return os.path.join(get_default_data_dir(), 'rsshub-routes.json')


def get_default_db_path():
    """获取默认数据库路径，跨平台支持"""
    # 优先使用环境变量
    env_db_path = os.environ.get('AIRSSTOOL_DB_PATH')
    if env_db_path:
        return env_db_path

    # 默认使用用户目录下的 .airsstool 文件夹（隐藏目录）
    home_dir = os.path.expanduser('~')
    return os.path.join(home_dir, '.airsstool', 'airsstoolDB.db')


def convert_heat_to_number(heat_str: str) -> int:
    """
    将热度字符串转换为数字，如 '1.4M' -> 1400000, '369.6K' -> 369600
    """
    if not heat_str:
        return 1

    heat_str = heat_str.strip().upper()

    try:
        if heat_str.endswith('M'):
            return int(float(heat_str[:-1]) * 1_000_000)
        elif heat_str.endswith('K'):
            return int(float(heat_str[:-1]) * 1_000)
        else:
            # 尝试直接解析为数字
            return int(float(heat_str))
    except (ValueError, AttributeError):
        return 1


def parse_html_for_heat(html_path: str) -> dict:
    """
    解析HTML文件，提取网站名称和热度值
    返回: {网站名: 热度值}
    """
    website_heat = {}

    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 使用正则表达式匹配每个namespace-card
    # 匹配模式: alt="网站名" 和 class="heat-badge">热度值
    card_pattern = re.compile(
        r'<a[^>]*class="namespace-card"[^>]*>.*?'
        r'<img[^>]*alt="([^"]+)"[^>]*>.*?'
        r'class="heat-badge">([^<]+)<',
        re.DOTALL
    )

    matches = card_pattern.findall(content)

    for name, heat_str in matches:
        heat_value = convert_heat_to_number(heat_str)
        website_heat[name] = heat_value

    return website_heat


def convert_heat_html_to_json(html_path: str, json_path: str = None) -> dict:
    """
    Utility function: Convert RSSHub's heat HTML file to JSON format.

    Args:
        html_path: Path to rsshub_routes_with_heat_badges.html
        json_path: Optional output path for JSON file. If not provided,
                   saves to same directory as html_path with .json extension.

    Returns:
        dict: Website heat data {website_name: heat_value}

    Example:
        convert_heat_html_to_json('rsshub_routes_with_heat_badges.html', 'heat.json')
    """
    if not os.path.exists(html_path):
        print(f"Error: HTML file not found at {html_path}")
        return {}

    print(f"Parsing {html_path}...")
    website_heat = parse_html_for_heat(html_path)
    print(f"Found heat values for {len(website_heat)} websites")

    # Determine output path
    if json_path is None:
        json_path = os.path.splitext(html_path)[0] + '.json'

    # Save to JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(website_heat, f, ensure_ascii=False, indent=2)

    print(f"Saved to {json_path}")

    # Show file sizes
    html_size = os.path.getsize(html_path) / 1024  # KB
    json_size = os.path.getsize(json_path) / 1024  # KB
    print(f"HTML size: {html_size:.1f} KB")
    print(f"JSON size: {json_size:.1f} KB")
    print(f"Size reduction: {(1 - json_size/html_size)*100:.1f}%")

    return website_heat


def fetch_categories_from_db(conn) -> dict:
    """
    从数据库获取所有分类
    返回: {category_name: id}
    """
    cursor = conn.cursor()
    cursor.execute('SELECT id, category FROM Category')
    return {row[1]: row[0] for row in cursor.fetchall()}


def add_website_to_db(conn, website_info: dict) -> int:
    """
    添加网站到数据库，返回网站ID
    """
    cursor = conn.cursor()

    # 处理可能是列表的值，转换为字符串
    name = website_info.get('name')
    if isinstance(name, list):
        name = name[0] if name else None
    url = website_info.get('url')
    if isinstance(url, list):
        url = url[0] if url else None
    description = website_info.get('description')
    if isinstance(description, list):
        description = description[0] if description else None
    lang = website_info.get('lang')
    if isinstance(lang, list):
        lang = lang[0] if lang else None

    cursor.execute('''
        INSERT INTO Website (name, url, description, lang, heat, nsfw)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        name,
        url,
        description,
        lang,
        website_info.get('heat', 1),
        1 if website_info.get('nsfw') else 0
    ))
    return cursor.lastrowid


def add_route_to_db(conn, website_id: int, route_info: dict) -> int:
    """
    添加路由到数据库，返回路由ID
    """
    cursor = conn.cursor()

    # 处理可能是列表的值，转换为字符串
    path = route_info.get('path')
    if isinstance(path, list):
        path = path[0] if path else None
    name = route_info.get('name')
    if isinstance(name, list):
        name = name[0] if name else None
    example = route_info.get('example')
    if isinstance(example, list):
        example = example[0] if example else None
    lang = route_info.get('lang')
    if isinstance(lang, list):
        lang = lang[0] if lang else None
    description = route_info.get('description')
    if isinstance(description, list):
        description = description[0] if description else None
    url = route_info.get('url')
    if isinstance(url, list):
        url = url[0] if url else None

    cursor.execute('''
        INSERT INTO Route (website_id, path, name, example, lang, description, url, requireConfig, nsfw)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        website_id,
        path,
        name,
        example,
        lang,
        description,
        url,
        1 if route_info.get('requireConfig') else 0,
        1 if route_info.get('nsfw') else 0
    ))
    return cursor.lastrowid


def add_config_to_db(conn, route_id: int, config: tuple):
    """
    添加配置到数据库
    config: (name, optional, description)
    """
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO RouteConfig (route_id, name, optional, description)
        VALUES (?, ?, ?, ?)
    ''', (route_id, config[0], 1 if config[1] else 0, config[2]))


def add_category_to_db(conn, category_name: str) -> int:
    """
    添加分类到数据库，返回分类ID
    """
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO Category (category, website_count, route_count)
        VALUES (?, 0, 0)
    ''', (category_name,))

    # 获取分类ID
    cursor.execute('SELECT id FROM Category WHERE category = ?', (category_name,))
    return cursor.fetchone()[0]


def add_route_category_to_db(conn, category_id: int, route_id: int):
    """
    添加路由-分类关联到数据库，并更新分类的路由计数
    """
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO RouteCategory (category_id, route_id)
        VALUES (?, ?)
    ''', (category_id, route_id))

    # 更新路由计数
    cursor.execute('''
        UPDATE Category SET route_count = route_count + 1
        WHERE id = ?
    ''', (category_id,))


def add_website_category_to_db(conn, category_id: int, website_id: int):
    """
    添加网站-分类关联到数据库，并更新分类的网站计数
    """
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO WebsiteCategory (category_id, website_id)
        VALUES (?, ?)
    ''', (category_id, website_id))

    # 更新网站计数
    cursor.execute('''
        UPDATE Category SET website_count = website_count + 1
        WHERE id = ?
    ''', (category_id,))


def add_route_parameter_to_db(conn, route_id: int, param: tuple) -> int:
    """
    添加路由参数到数据库
    param: (name, description, default, has_options)
    返回参数ID
    """
    cursor = conn.cursor()

    # 处理可能是列表的值，转换为字符串
    name = param[0]
    if isinstance(name, list):
        name = name[0] if name else None
    description = param[1]
    if isinstance(description, list):
        description = description[0] if description else None
    default = param[2]
    if isinstance(default, list):
        default = default[0] if default else None

    cursor.execute('''
        INSERT OR IGNORE INTO RouteParameter (route_id, name, description, default_value, has_options)
        VALUES (?, ?, ?, ?, ?)
    ''', (route_id, name, description, default, 1 if param[3] else 0))

    # 获取参数ID
    cursor.execute('SELECT id FROM RouteParameter WHERE route_id = ? AND name = ?', (route_id, name))
    return cursor.fetchone()[0]


def add_route_parameter_option_to_db(conn, parameter_id: int, option: tuple):
    """
    添加路由参数选项到数据库
    option: (label, value)
    """
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO RouteParameterOption (parameter_id, label, value)
        VALUES (?, ?, ?)
    ''', (parameter_id, option[0], option[1]))


def process_rsshub_data(db_path: str = None):
    """
    主函数：处理RSSHub数据并导入数据库
    """
    if db_path is None:
        db_path = get_default_db_path()

    # 确保数据目录存在
    data_dir = get_default_data_dir()
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    routes_json_path = get_routes_json_path()

    # 1. 下载或加载routes JSON
    routes = None
    routes_downloaded = False

    if os.path.exists(routes_json_path):
        print(f"Loading existing routes from {routes_json_path}...")
        with open(routes_json_path, 'r', encoding='utf-8') as f:
            routes = json.load(f)
    else:
        # 尝试从RSSHub API下载
        print(f"Downloading routes from {RSSHUB_URL}/api/namespace...")
        try:
            with httpx.Client(timeout=30.0, follow_redirects=True, trust_env=False) as client:
                response = client.get(f"{RSSHUB_URL}/api/namespace")
                response.raise_for_status()
                routes = response.json()
                routes_downloaded = True

                # 保存到本地
                with open(routes_json_path, 'w', encoding='utf-8') as f:
                    json.dump(routes, f, ensure_ascii=False)
                print(f"Saved routes to {routes_json_path}")
        except Exception as e:
            print(f"Error downloading routes: {e}")

    if routes is None:
        print("Error: Could not load routes data. Initialization failed.")
        return False

    # 2. 加载热度数据
    website_heat = {}

    if os.path.exists(HEAT_JSON_PATH):
        print(f"Loading heat data from {HEAT_JSON_PATH}...")
        with open(HEAT_JSON_PATH, 'r', encoding='utf-8') as f:
            website_heat = json.load(f)

    print(f"Found heat values for {len(website_heat)} websites")

    # 3. 连接数据库
    conn = sqlite3.connect(db_path)

    # 获取现有分类
    category_name_id = fetch_categories_from_db(conn)

    # 统计计数
    website_count = 0
    route_count = 0

    # 4. 遍历routes并导入数据库
    print("开始导入数据到数据库...")

    for website_key, website_data in routes.items():
        website_info = defaultdict(lambda: None)
        website_categories = set()
        website_has_nsfw_route = False  # 跟踪网站是否有nsfw路由

        # 跳过没有routes的网站
        if 'routes' not in website_data or not website_data['routes']:
            continue

        website_info['name'] = website_data.get('name', website_key)
        website_info['url'] = website_data.get('url')
        website_info['description'] = website_data.get('description')
        website_info['lang'] = website_data.get('lang')

        # 设置热度值
        if website_info['name'] in website_heat:
            website_info['heat'] = website_heat[website_info['name']]
        else:
            website_info['heat'] = 1

        # 添加网站到数据库（先不设置nsfw，后面会更新）
        website_id = add_website_to_db(conn, website_info)
        website_count += 1

        # 检查网站是否有categories
        if 'categories' in website_data:
            website_categories.update(website_data['categories'])

        # 遍历routes
        for route_key, route_data in website_data['routes'].items():
            configs = []
            route_categories = set()
            route_info = defaultdict(lambda: None)

            route_info['path'] = route_data.get('path', route_key)
            route_info['name'] = route_data.get('name', route_key)
            route_info['example'] = route_data.get('example')
            route_info['lang'] = route_data.get('lang')
            route_info['description'] = route_data.get('description')
            route_info['url'] = route_data.get('url')
            route_info['requireConfig'] = False
            route_info['nsfw'] = False

            # 更新分类
            if 'categories' in route_data:
                route_categories.update(route_data['categories'])
                website_categories.update(route_data['categories'])

            # 处理features
            if 'features' in route_data:
                features = route_data['features']
                if features.get('nsfw'):
                    route_info['nsfw'] = True
                    website_has_nsfw_route = True  # 标记网站有nsfw路由
                if 'requireConfig' in features:
                    requireConfig = features['requireConfig']
                    if isinstance(requireConfig, list):
                        route_info['requireConfig'] = True
                        for cfg in requireConfig:
                            configs.append((
                                cfg.get('name'),
                                cfg.get('optional', False),
                                cfg.get('description', '')
                            ))

            # 添加路由到数据库
            route_id = add_route_to_db(conn, website_id, route_info)
            route_count += 1

            # 添加configs
            for cfg in configs:
                add_config_to_db(conn, route_id, cfg)

            # 添加路由分类
            for cat in route_categories:
                if cat not in category_name_id:
                    category_name_id[cat] = add_category_to_db(conn, cat)
                add_route_category_to_db(conn, category_name_id[cat], route_id)

            # 添加路由参数
            if 'parameters' in route_data:
                for param_name, param_desc in route_data['parameters'].items():
                    has_options = False
                    parameter_options = []
                    default = None

                    if isinstance(param_desc, dict):
                        description = param_desc.get('description')
                        default = param_desc.get('default')
                        if param_desc.get('options'):
                            has_options = True
                            for opt in param_desc['options']:
                                parameter_options.append((opt.get('label'), opt.get('value')))
                    else:
                        description = param_desc

                    parameter_id = add_route_parameter_to_db(
                        conn, route_id,
                        (param_name, description, default, has_options)
                    )

                    # 添加参数选项
                    for opt in parameter_options:
                        add_route_parameter_option_to_db(conn, parameter_id, opt)

        # 更新网站的nsfw状态
        if website_has_nsfw_route:
            cursor = conn.cursor()
            cursor.execute('UPDATE Website SET nsfw = 1 WHERE id = ?', (website_id,))

        # 添加网站分类
        if len(website_categories) == 0:
            # 如果网站没有分类，则添加到 Unspecified 分类
            if 'Unspecified' not in category_name_id:
                category_name_id['Unspecified'] = add_category_to_db(conn, 'Unspecified')
            add_website_category_to_db(conn, category_name_id['Unspecified'], website_id)
        else:
            for cat in website_categories:
                if cat not in category_name_id:
                    category_name_id[cat] = add_category_to_db(conn, cat)
                add_website_category_to_db(conn, category_name_id[cat], website_id)

        # 每处理100个网站提交一次并显示进度
        if website_count % 100 == 0:
            conn.commit()
            print(f"Processed {website_count} websites, {route_count} routes...")

    # 提交所有更改
    conn.commit()
    conn.close()

    print(f"\nImport completed!")
    print(f"Total: {website_count} websites, {route_count} routes")
    print(f"Database: {db_path}")

    # 清理：删除下载的routes JSON（如果是从网络下载的）
    if routes_downloaded and os.path.exists(routes_json_path):
        os.remove(routes_json_path)
        print(f"Cleaned up temporary file: {routes_json_path}")

    return True


if __name__ == '__main__':
    process_rsshub_data()