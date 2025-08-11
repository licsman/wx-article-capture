import csv
import mysql.connector
from mysql.connector import Error
import argparse
import os
from datetime import datetime

def create_connection(host, database, user, password, port=3306):
    """创建MySQL数据库连接"""
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


def insert_data_from_csv(connection, csv_file_path):
    """从CSV文件读取数据并插入到MySQL数据库"""
    try:
        cursor = connection.cursor()

        # SQL插入语句
        insert_query = """
        INSERT INTO article_link_info (account_name, title, link, release_date, is_free, collect_time)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        # 读取CSV文件并插入数据
        with open(csv_file_path, 'r', encoding='utf-8-sig') as file:
            csv_reader = csv.reader(file)

            # 跳过标题行
            next(csv_reader)

            row_count = 0
            for row in csv_reader:
                # 检查行是否有足够的列
                if len(row) < 6:
                    continue

                # 提取数据
                account_name, title, link, release_date, is_free, collect_time = row

                # 跳过空行
                if not account_name or not title or not link or not release_date:
                    continue

                # 处理is_free字段
                try:
                    is_free_int = int(is_free)
                except ValueError:
                    is_free_int = 1  # 默认为免费

                # 处理collect_time字段
                try:
                    collect_time_dt = datetime.strptime(collect_time, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    collect_time_dt = datetime.now()

                # 插入数据
                try:
                    cursor.execute(insert_query, (
                        account_name,
                        title,
                        link,
                        release_date,
                        is_free_int,
                        collect_time_dt
                    ))
                    row_count += 1
                except Error as e:
                    print(f"插入行时出错: {e}")
                    print(f"数据: {row}")
                    continue

            connection.commit()
            print(f"成功插入 {row_count} 条记录")

    except Exception as e:
        print(f"插入数据时出错: {e}")
        connection.rollback()
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()


def main():
    # 创建参数解析器
    parser = argparse.ArgumentParser(description='将CSV文件数据导入MySQL数据库')
    parser.add_argument('--host', required=True, help='MySQL服务器地址')
    parser.add_argument('--database', required=True, help='数据库名称')
    parser.add_argument('--user', required=True, help='用户名')
    parser.add_argument('--password', required=True, help='密码')
    parser.add_argument('--port', type=int, default=3306, help='端口号 (默认: 3306)')
    parser.add_argument('--csv-file', required=False, help='CSV文件路径')

    # 解析命令行参数
    args = parser.parse_args()
    args.csv_file = \
        "/Users/houmengqi/code/wx-article-capture/wx_links_20250809180418.csv"

    # 检查CSV文件是否存在
    if not os.path.exists(args.csv_file):
        print(f"文件 {args.csv_file} 不存在")
        return

    # 创建数据库连接
    connection = create_connection(args.host, args.database, args.user, args.password, args.port)
    if not connection:
        return

    try:
        # 插入数据
        insert_data_from_csv(connection, args.csv_file)
        print("数据导入完成")
    except Exception as e:
        print(f"导入过程中出错: {e}")
    finally:
        # 关闭数据库连接
        if connection.is_connected():
            connection.close()
            print("MySQL连接已关闭")


if __name__ == "__main__":
    main()