#!/usr/bin/env python3
"""
airsstool - RSSHub CLI Tool

Usage:
    airsstool list categories
    airsstool list websites [-C/--category=xx] [-PS/--page_size=xx] [-PN/--page_num=xx]
    airsstool list routes <website>
    airsstool list subscriptions -U/--user=xxx
    airsstool list paths -U/--user=xxx -S/--subscription=xxx
    airsstool list users
    airsstool check <website> <route>
    airsstool fetch -P/--path=xxx [-L/--limit=N] [-O/--offset=N]
    airsstool fetch -U/--user=xxx -S/--subscription=xxx [-L/--limit=N] [-O/--offset=N]
    airsstool subscribe -U/--user=xxx -S/--subscription=xxx -P/--path=xxx -D/--description=xxx
    airsstool add-subscription -U/--user=xxx -S/--subscription=xxx
    airsstool -h/--help
"""

import argparse
import sys
import os

from .airsstool_mcp import (
    list_rss_categories,
    list_rss_websites,
    list_rss_routes,
    check_rss_route_detail,
    fetch_rss,
    list_users,
    list_rss_subscription,
    list_rss_subscribed_paths,
    add_rss_subscription,
    subscribe_rss_path,
    fetch_rss_subscription,
)


def cmd_list(args):
    """处理 list 子命令"""
    if args.list_type == 'categories':
        print(list_rss_categories())
    elif args.list_type == 'websites':
        print(list_rss_websites(
            category=args.category,
            page_size=args.page_size,
            page_num=args.page_num,
            enable_nsfw=args.enable_nsfw
        ))
    elif args.list_type == 'routes':
        if not args.website:
            print("Error: --website is required for listing routes")
            print("Use 'airsstool list routes <website>' or 'airsstool list -h' for more information.")
            sys.exit(1)
        print(list_rss_routes(args.website))
    elif args.list_type == 'subscriptions':
        if not args.user:
            print("Error: --user is required for listing subscriptions")
            print("Use 'airsstool list subscriptions --user USER' or 'airsstool list -h' for more information.")
            sys.exit(1)
        print(list_rss_subscription(args.user))
    elif args.list_type == 'paths':
        if not args.user or not args.subscription:
            print("Error: --user and --subscription are required for listing paths")
            print("Use 'airsstool list paths --user USER --subscription NAME' or 'airsstool list -h' for more information.")
            sys.exit(1)
        print(list_rss_subscribed_paths(args.user, args.subscription))
    elif args.list_type == 'users':
        print(list_users())


def cmd_check(args):
    """处理 check 子命令"""
    if len(args.args) < 2:
        print("Error: check requires <website> <route>")
        print("Use 'airsstool check <website> <route>' or 'airsstool check -h' for more information.")
        sys.exit(1)
    website = args.args[0]
    route = args.args[1]
    print(check_rss_route_detail(website, route))


def cmd_fetch(args):
    """处理 fetch 子命令"""
    # 构建参数字典
    fetch_kwargs = {
        'limit': args.limit,
        'offset': args.offset,
        'filter': args.filter,
        'filter_title': args.filter_title,
        'filter_description': args.filter_description,
        'filter_author': args.filter_author,
        'filter_category': args.filter_category,
        'filter_time': args.filter_time,
        'filterout': args.filterout,
        'filterout_title': args.filterout_title,
        'filterout_description': args.filterout_description,
        'filterout_author': args.filterout_author,
        'filterout_category': args.filterout_category,
        'filter_case_sensitive': args.filter_case_sensitive,
        'format': args.format,
        'brief': args.brief,
    }

    # 优先使用位置参数 path_arg，其次使用 --path 选项
    path = args.path_arg or args.path

    if path:
        print(fetch_rss(path, **fetch_kwargs))
    elif args.user and args.subscription:
        print(fetch_rss_subscription(args.user, args.subscription, **fetch_kwargs))
    else:
        print("Error: fetch requires either a path or both --user and --subscription")
        print("Use 'airsstool fetch <path>' or 'airsstool fetch --user USER --subscription NAME'.")
        print("See 'airsstool fetch -h' for more information.")
        sys.exit(1)


def cmd_subscribe(args):
    """处理 subscribe 子命令"""
    print(subscribe_rss_path(args.user, args.subscription, args.description, args.path, args.force))


def cmd_add_subscription(args):
    """处理 add-subscription 子命令"""
    print(add_rss_subscription(args.user, args.subscription))


def cmd_init(args):
    """处理 init 子命令"""
    from .db_creation import create_database
    from .process_rsshub_data import process_rsshub_data, get_default_db_path

    db_path = args.db_path if args.db_path else get_default_db_path()

    # 检查数据库是否已存在
    if os.path.exists(db_path):
        if not args.force:
            print(f"Database already exists at: {db_path}")
            print("Use --force to recreate the database (this will delete existing data).")
            return
        else:
            print(f"Deleting existing database: {db_path}")
            os.remove(db_path)

    print(f"Initializing airsstool database at: {db_path}")

    # 创建数据库
    create_database(db_path)

    # 导入数据
    process_rsshub_data(db_path)

    print("\nInitialization complete!")
    print(f"Database location: {db_path}")


def main():
    parser = argparse.ArgumentParser(
        description='airsstool - RSSHub CLI Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    airsstool list categories
    airsstool list websites --category programming --page-size 10
    airsstool list routes youtube
    airsstool check youtube user
    airsstool fetch /github/trending/daily/any/en
    airsstool fetch /youtube/user/@MrBeast --limit 5
    airsstool fetch /hackernews/best --format rss --limit 10
    airsstool fetch /instagram/user/instagram --brief 100
    airsstool list subscriptions --user alice
    airsstool add-subscription --user alice --subscription tech_news
    airsstool subscribe --user alice --subscription tech_news --path /github/trending/daily/javascript/en --description "GitHub JS Daily Trending"
    airsstool fetch --user alice --subscription tech_news
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # init 子命令
    init_parser = subparsers.add_parser(
        'init',
        help='Initialize airsstool database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''
Initialize airsstool database.

This command creates the database and imports RSSHub routes data.

Usage:
  airsstool init                    Initialize with default path (~/.airsstool/airsstoolDB.db)
  airsstool init --db-path PATH     Initialize with custom path
  airsstool init --force            Force recreate (deletes existing database)

Examples:
  airsstool init
  airsstool init --db-path /custom/path/airsstoolDB.db
  airsstool init --force
        '''
    )
    init_parser.add_argument('--db-path', metavar='PATH', help='Custom database path')
    init_parser.add_argument('--force', action='store_true', help='Force recreate database (deletes existing)')
    init_parser.set_defaults(func=cmd_init)

    # list 子命令
    list_parser = subparsers.add_parser(
        'list',
        help='List various resources',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''
List various RSSHub resources.

Types:
  categories     List all RSS categories
  websites       List websites (use --category to filter)
  routes         List routes for a website
  subscriptions  List user's subscriptions
  paths          List paths in a subscription
  users          List all users

Usage:
  airsstool list categories
  airsstool list websites [--category CAT] [--page-size N] [--page-num N] [--enable-nsfw]
  airsstool list routes <website>
  airsstool list subscriptions --user USER
  airsstool list paths --user USER --subscription SUBSCRIPTION
  airsstool list users
        '''
    )
    list_parser.add_argument('list_type', choices=['categories', 'websites', 'routes', 'subscriptions', 'paths', 'users'],
                             help='Type of resource to list')
    list_parser.add_argument('website', nargs='?', help='Website name (for routes)')
    list_parser.add_argument('-C', '--category', metavar='CAT', help='Filter by category')
    list_parser.add_argument('-PS', '--page-size', metavar='N', type=int, default=20, help='Page size (default: 20)')
    list_parser.add_argument('-PN', '--page-num', metavar='N', type=int, default=1, help='Page number (default: 1)')
    list_parser.add_argument('-U', '--user', metavar='USER', help='User name')
    list_parser.add_argument('-S', '--subscription', metavar='NAME', help='Subscription name')
    list_parser.add_argument('--enable-nsfw', action='store_true', help='Include NSFW websites')
    list_parser.set_defaults(func=cmd_list)

    # check 子命令
    check_parser = subparsers.add_parser(
        'check',
        help='Check route details',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''
Check detailed information about a route.

Usage:
  airsstool check <website> <route>

Example:
  airsstool check github trending
        '''
    )
    check_parser.add_argument('args', nargs='*', help='<website> <route>')
    check_parser.set_defaults(func=cmd_check)

    # fetch 子命令
    fetch_parser = subparsers.add_parser(
        'fetch',
        help='Fetch RSS content',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''
Fetch RSS content from a path or subscription.

Usage:
  airsstool fetch <path>                               Fetch from a single path
  airsstool fetch --user <user> --subscription <name>  Fetch from a subscription

Output Options:
  --format FORMAT    Output format: markdown (default), rss, atom, json, rss3
  --brief N          Output brief text with N chars (>=100)
  --limit N          Limit number of feeds (when format is not markdown, adds to URL params)
  --offset N         Skip first N feeds (only works with markdown format)

Filter Options (select content):
  --filter PATTERN       Filter title and description
  --filter-title PATTERN Filter title only
  --filter-description PATTERN Filter description only
  --filter-author PATTERN    Filter author
  --filter-category PATTERN  Filter category
  --filter-time SECONDS  Filter by time range

Filterout Options (exclude content):
  --filterout PATTERN       Exclude from title and description
  --filterout-title PATTERN Exclude from title
  --filterout-description PATTERN Exclude from description
  --filterout-author PATTERN    Exclude author
  --filterout-category PATTERN  Exclude category

Other:
  --filter-case-sensitive BOOL  Filter case sensitivity (default: true)

Note: --user and --subscription must be used together.

Examples:
  airsstool fetch /github/trending/daily/javascript/en
  airsstool fetch /github/trending/daily/any/en --limit 5 --offset 2
  airsstool fetch /youtube/user/@MrBeast --filter "MrBeast|Beast"
  airsstool fetch /hackernews/best --format rss --limit 10
  airsstool fetch /instagram/user/instagram --format atom
  airsstool fetch /instagram/user/instagram --brief 100
  airsstool fetch --user alice --subscription tech_news --limit 10
        '''
    )
    # 位置参数（可选的path）
    fetch_parser.add_argument('path_arg', nargs='?', metavar='PATH', help='RSS path to fetch (positional)')
    # 基本参数
    fetch_parser.add_argument('-P', '--path', metavar='PATH', help='RSS path to fetch (alternative to positional)')
    fetch_parser.add_argument('-U', '--user', metavar='USER', help='User name (requires --subscription)')
    fetch_parser.add_argument('-S', '--subscription', metavar='NAME', help='Subscription name (requires --user)')
    fetch_parser.add_argument('-L', '--limit', metavar='N', type=int, default=0, help='Limit number of feeds (0 = all)')
    fetch_parser.add_argument('-O', '--offset', metavar='N', type=int, default=0, help='Skip first N feeds')

    # 过滤参数
    fetch_parser.add_argument('--filter', metavar='PATTERN', help='Filter title and description')
    fetch_parser.add_argument('--filter-title', metavar='PATTERN', help='Filter title only')
    fetch_parser.add_argument('--filter-description', metavar='PATTERN', help='Filter description only')
    fetch_parser.add_argument('--filter-author', metavar='PATTERN', help='Filter author')
    fetch_parser.add_argument('--filter-category', metavar='PATTERN', help='Filter category')
    fetch_parser.add_argument('--filter-time', metavar='SECONDS', type=int, help='Filter by time range (seconds)')

    # 排除参数
    fetch_parser.add_argument('--filterout', metavar='PATTERN', help='Exclude from title and description')
    fetch_parser.add_argument('--filterout-title', metavar='PATTERN', help='Exclude from title')
    fetch_parser.add_argument('--filterout-description', metavar='PATTERN', help='Exclude from description')
    fetch_parser.add_argument('--filterout-author', metavar='PATTERN', help='Exclude author')
    fetch_parser.add_argument('--filterout-category', metavar='PATTERN', help='Exclude category')

    # 其他参数
    fetch_parser.add_argument('--filter-case-sensitive', type=lambda x: x.lower() == 'true', help='Filter case sensitivity (true/false)')
    fetch_parser.add_argument('--format', choices=['markdown', 'rss', 'atom', 'json', 'rss3'], help='Output format (default: markdown)')
    fetch_parser.add_argument('--brief', metavar='N', type=int, help='Output brief text with N chars (>=100)')

    fetch_parser.set_defaults(func=cmd_fetch)

    # subscribe 子命令
    subscribe_parser = subparsers.add_parser(
        'subscribe',
        help='Subscribe to a feed path',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''
Add a RSS path to a user's subscription.

Usage:
  airsstool subscribe --user <user> --subscription <name> --path <path> --description <desc>
  airsstool subscribe ... --force   Skip connectivity check

Examples:
  airsstool subscribe --user alice --subscription tech_news --path /github/trending/daily/javascript/en --description "GitHub Daily Trending"
  airsstool subscribe --user alice --subscription tech_news --path /github/trending/daily/any/en --description "Test" --force
        '''
    )
    subscribe_parser.add_argument('-U', '--user', metavar='USER', required=True, help='User name')
    subscribe_parser.add_argument('-S', '--subscription', metavar='NAME', required=True, help='Subscription name')
    subscribe_parser.add_argument('-P', '--path', metavar='PATH', required=True, help='RSS path')
    subscribe_parser.add_argument('-D', '--description', metavar='DESC', required=True, help='Path description')
    subscribe_parser.add_argument('--force', action='store_true', help='Force add without connectivity check')
    subscribe_parser.set_defaults(func=cmd_subscribe)

    # add-subscription 子命令
    add_sub_parser = subparsers.add_parser(
        'add-subscription',
        help='Add a new subscription',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''
Create a new subscription for a user.

Usage:
  airsstool add-subscription --user <user> --subscription <name>

Example:
  airsstool add-subscription --user alice --subscription tech_news
        '''
    )
    add_sub_parser.add_argument('-U', '--user', metavar='USER', required=True, help='User name')
    add_sub_parser.add_argument('-S', '--subscription', metavar='NAME', required=True, help='Subscription name')
    add_sub_parser.set_defaults(func=cmd_add_subscription)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == '__main__':
    main()