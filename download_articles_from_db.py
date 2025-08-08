import sys

import mysql.connector
from mysql.connector import Error
from datetime import datetime
from typing import List, Optional, Union
import argparse

from mysql.connector.abstracts import MySQLConnectionAbstract
from mysql.connector.pooling import PooledMySQLConnection


class ArticleInfo:
    """
    文章信息实体类
    """

    def __init__(self, id: int = None, account_name: str = "", title: str = "", link: str = "",
                 release_date: str = "", is_free: int = 1, collect_time: datetime = None):
        self.id = id
        self.account_name = account_name
        self.title = title
        self.link = link
        self.release_date = release_date
        self.is_free = is_free  # 1代表免费，0代表付费
        self.collect_time = collect_time

    def __str__(self):
        return f"ArticleInfo(id={self.id}, account_name='{self.account_name}', title='{self.title}', " \
               f"link='{self.link}', release_date='{self.release_date}', is_free={self.is_free}, " \
               f"collect_time={self.collect_time})"

    def __repr__(self):
        return self.__str__()


def create_connection(host: str, database: str, user: str, password: str,
                      port: int = 3306) -> Union[None, PooledMySQLConnection, MySQLConnectionAbstract]:
    """
    创建MySQL数据库连接

    Args:
        host: MySQL服务器地址
        database: 数据库名称
        user: 用户名
        password: 密码
        port: 端口号

    Returns:
        MySQL连接对象或None
    """
    try:
        connection = mysql.connector.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        if connection.is_connected():
            print(f"成功连接到MySQL数据库 {database}")
            return connection
    except Error as e:
        print(f"连接MySQL时出错: {e}")
        return None


def get_all_articles(connection) -> List[ArticleInfo]:
    """
    从数据库中获取所有文章信息

    Args:
        connection: MySQL数据库连接对象

    Returns:
        List[ArticleInfo]: 文章信息实体列表
    """
    articles = []
    try:
        cursor = connection.cursor()

        # SQL查询语句
        select_query = """
                       SELECT id, account_name, title, link, release_date, is_free, collect_time
                       FROM article_link_info
                       ORDER BY collect_time DESC \
                       """

        cursor.execute(select_query)
        records = cursor.fetchall()

        # 将查询结果转换为ArticleInfo对象列表
        for row in records:
            article = ArticleInfo(
                id=row[0],
                account_name=row[1],
                title=row[2],
                link=row[3],
                release_date=row[4],
                is_free=row[5],
                collect_time=row[6]
            )
            articles.append(article)

        print(f"成功查询到 {len(articles)} 条文章记录")

    except Error as e:
        print(f"查询数据时出错: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()

    return articles


def get_articles_by_account(connection, account_name: str) -> List[ArticleInfo]:
    """
    根据账号名称获取文章信息

    Args:
        connection: MySQL数据库连接对象
        account_name: 账号名称

    Returns:
        List[ArticleInfo]: 文章信息实体列表
    """
    articles = []
    try:
        cursor = connection.cursor()

        # SQL查询语句
        select_query = """
                       SELECT id, account_name, title, link, release_date, is_free, collect_time
                       FROM article_link_info
                       WHERE account_name = %s
                       ORDER BY collect_time DESC \
                       """

        cursor.execute(select_query, (account_name,))
        records = cursor.fetchall()

        # 将查询结果转换为ArticleInfo对象列表
        for row in records:
            article = ArticleInfo(
                id=row[0],
                account_name=row[1],
                title=row[2],
                link=row[3],
                release_date=row[4],
                is_free=row[5],
                collect_time=row[6]
            )
            articles.append(article)

        print(f"账号 '{account_name}' 共查询到 {len(articles)} 条文章记录")

    except Error as e:
        print(f"查询数据时出错: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()

    return articles


def get_free_articles(connection) -> List[ArticleInfo]:
    """
    获取所有免费文章信息

    Args:
        connection: MySQL数据库连接对象

    Returns:
        List[ArticleInfo]: 免费文章信息实体列表
    """
    articles = []
    try:
        cursor = connection.cursor()

        # SQL查询语句
        select_query = """
                       SELECT id, account_name, title, link, release_date, is_free, collect_time
                       FROM article_link_info
                       WHERE is_free = 1
                       ORDER BY collect_time DESC \
                       """

        cursor.execute(select_query)
        records = cursor.fetchall()

        # 将查询结果转换为ArticleInfo对象列表
        for row in records:
            article = ArticleInfo(
                id=row[0],
                account_name=row[1],
                title=row[2],
                link=row[3],
                release_date=row[4],
                is_free=row[5],
                collect_time=row[6]
            )
            articles.append(article)

        print(f"共查询到 {len(articles)} 条免费文章记录")

    except Error as e:
        print(f"查询数据时出错: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()

    return articles


def get_paid_articles(connection) -> List[ArticleInfo]:
    """
    获取所有付费文章信息

    Args:
        connection: MySQL数据库连接对象

    Returns:
        List[ArticleInfo]: 付费文章信息实体列表
    """
    articles = []
    try:
        cursor = connection.cursor()

        # SQL查询语句
        select_query = """
                       SELECT id, account_name, title, link, release_date, is_free, collect_time
                       FROM article_link_info
                       WHERE is_free = 0
                       ORDER BY collect_time DESC \
                       """

        cursor.execute(select_query)
        records = cursor.fetchall()

        # 将查询结果转换为ArticleInfo对象列表
        for row in records:
            article = ArticleInfo(
                id=row[0],
                account_name=row[1],
                title=row[2],
                link=row[3],
                release_date=row[4],
                is_free=row[5],
                collect_time=row[6]
            )
            articles.append(article)

        print(f"共查询到 {len(articles)} 条付费文章记录")

    except Error as e:
        print(f"查询数据时出错: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()

    return articles


def print_articles(articles: List[ArticleInfo]):
    """
    打印文章信息列表

    Args:
        articles: 文章信息列表
    """
    if not articles:
        print("没有文章数据")
        return

    print(f"\n{'ID':<5} {'账号名称':<15} {'标题':<30} {'链接':<50} {'发布日期':<12} {'是否免费':<8} {'采集时间':<20}")
    print("-" * 150)

    for article in articles:
        is_free_text = "是" if article.is_free == 1 else "否"
        title_short = article.title[:28] + "..." if len(article.title) > 28 else article.title
        link_short = article.link[:48] + "..." if len(article.link) > 48 else article.link

        print(f"{article.id:<5} {article.account_name:<15} {title_short:<30} {link_short:<50} "
              f"{article.release_date:<12} {is_free_text:<8} {article.collect_time}")


if __name__ == '__main__':
    # 创建参数解析器
    parser = argparse.ArgumentParser(description='从MySQL数据库查询文章信息')
    parser.add_argument('--host', required=True, help='MySQL服务器地址')
    parser.add_argument('--database', required=True, help='数据库名称')
    parser.add_argument('--user', required=True, help='用户名')
    parser.add_argument('--password', required=True, help='密码')
    parser.add_argument('--port', type=int, default=3306, help='端口号 (默认: 3306)')

    # 解析命令行参数
    args = parser.parse_args()

    # 创建数据库连接
    connection = create_connection(args.host, args.database, args.user, args.password, args.port)
    if not connection:
        print("无法连接到MySQL数据库")
        sys.exit(1)

    try:
        # 获取所有文章
        all_articles = get_all_articles(connection)
        print(f"总共获取到 {len(all_articles)} 篇文章")
        print_articles(all_articles)

    except Exception as e:
        print(f"查询过程中出错: {e}")
    finally:
        # 关闭数据库连接
        if connection.is_connected():
            connection.close()
            print("MySQL连接已关闭")


