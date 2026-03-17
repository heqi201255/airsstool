import sqlite3
import os

# 默认数据库路径 (会被 get_default_db_path 覆盖)
DEFAULT_DB_PATH = None


def get_default_db_path():
    """获取默认数据库路径，跨平台支持"""
    # 优先使用环境变量
    env_db_path = os.environ.get('AIRSSTOOL_DB_PATH')
    if env_db_path:
        return env_db_path

    # 默认使用用户目录下的 .airsstool 文件夹（隐藏目录）
    home_dir = os.path.expanduser('~')
    return os.path.join(home_dir, '.airsstool', 'airsstoolDB.db')


def create_database(db_path: str = None):
    """创建RSSHub数据库及所有表"""
    if db_path is None:
        db_path = get_default_db_path()

    # 确保目录存在
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建Category表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Category (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL UNIQUE,
            website_count INTEGER DEFAULT 0,
            route_count INTEGER DEFAULT 0
        )
    ''')

    # 创建Website表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Website (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT,
            description TEXT,
            lang TEXT,
            heat INTEGER DEFAULT 1,
            nsfw INTEGER DEFAULT 0
        )
    ''')

    # 创建Route表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Route (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            website_id INTEGER NOT NULL,
            path TEXT,
            name TEXT,
            example TEXT,
            lang TEXT,
            description TEXT,
            url TEXT,
            requireConfig INTEGER DEFAULT 0,
            nsfw INTEGER DEFAULT 0,
            FOREIGN KEY (website_id) REFERENCES Website(id)
        )
    ''')

    # 创建WebsiteCategory表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS WebsiteCategory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            website_id INTEGER NOT NULL,
            FOREIGN KEY (category_id) REFERENCES Category(id),
            FOREIGN KEY (website_id) REFERENCES Website(id),
            UNIQUE(category_id, website_id)
        )
    ''')

    # 创建RouteCategory表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS RouteCategory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            route_id INTEGER NOT NULL,
            FOREIGN KEY (category_id) REFERENCES Category(id),
            FOREIGN KEY (route_id) REFERENCES Route(id),
            UNIQUE(category_id, route_id)
        )
    ''')

    # 创建RouteParameter表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS RouteParameter (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_id INTEGER NOT NULL,
            name TEXT,
            description TEXT,
            default_value TEXT,
            has_options INTEGER DEFAULT 0,
            FOREIGN KEY (route_id) REFERENCES Route(id),
            UNIQUE(route_id, name)
        )
    ''')

    # 创建RouteParameterOption表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS RouteParameterOption (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parameter_id INTEGER NOT NULL,
            label TEXT,
            value TEXT,
            FOREIGN KEY (parameter_id) REFERENCES RouteParameter(id),
            UNIQUE(parameter_id, label)
        )
    ''')

    # 创建RouteConfig表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS RouteConfig (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            route_id INTEGER NOT NULL,
            name TEXT,
            optional INTEGER DEFAULT 0,
            description TEXT,
            FOREIGN KEY (route_id) REFERENCES Route(id),
            UNIQUE(route_id, name)
        )
    ''')

    # 创建UserSubscription表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS UserSubscription (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            subscription_name TEXT NOT NULL,
            route_count INTEGER DEFAULT 0,
            UNIQUE(user, subscription_name)
        )
    ''')

    # 创建SubscribedPath表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS SubscribedPath (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subscription_id INTEGER NOT NULL,
            description TEXT,
            path TEXT NOT NULL,
            FOREIGN KEY (subscription_id) REFERENCES UserSubscription(id)
        )
    ''')

    # 插入默认的'Unspecified'分类
    cursor.execute('''
        INSERT OR IGNORE INTO Category (category, website_count, route_count)
        VALUES ('Unspecified', 0, 0)
    ''')

    # 创建索引以加速检索
    # Website表索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_website_name ON Website(name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_website_heat ON Website(heat)')

    # Route表索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_route_website_id ON Route(website_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_route_name ON Route(name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_route_path ON Route(path)')

    # WebsiteCategory表索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_websitecategory_category_id ON WebsiteCategory(category_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_websitecategory_website_id ON WebsiteCategory(website_id)')

    # RouteCategory表索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_routecategory_category_id ON RouteCategory(category_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_routecategory_route_id ON RouteCategory(route_id)')

    # RouteParameter表索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_routeparameter_route_id ON RouteParameter(route_id)')

    # RouteParameterOption表索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_routeparameteroption_parameter_id ON RouteParameterOption(parameter_id)')

    # RouteConfig表索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_routeconfig_route_id ON RouteConfig(route_id)')

    # UserSubscription表索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_usersubscription_user ON UserSubscription(user)')

    # SubscribedPath表索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_subscribedpath_subscription_id ON SubscribedPath(subscription_id)')

    conn.commit()
    conn.close()
    print(f"Database created: {db_path}")
    return db_path


if __name__ == '__main__':
    create_database()