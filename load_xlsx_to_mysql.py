import pandas as pd
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


def insert_data_from_xlsx(connection, xlsx_file_path, account_name):
    """从XLSX文件读取数据并插入到MySQL数据库"""
    try:
        cursor = connection.cursor()

        # SQL插入语句
        insert_query = """
                       INSERT INTO articles (sys_id, account_name, url, title, cover_image, summary, create_time, publish_time, \
                                             read_count, like_count, share_count, favorite_count, comment_count, \
                                             author, is_original, article_type, collection, content) \
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       """

        # 读取XLSX文件
        df = pd.read_excel(xlsx_file_path)

        print(f"从XLSX文件中读取到 {len(df)} 行数据")

        row_count = 0
        success_count = 0
        skip_count = 0

        # 遍历每一行数据
        for index, row in df.iterrows():
            row_count += 1
            try:
                # 提取数据并处理空值
                sys_id = str(row['ID']) if pd.notna(row['ID']) else None
                url = row['链接'] if pd.notna(row['链接']) else None
                title = row['标题'] if pd.notna(row['标题']) else None
                cover_image = row['封面'] if pd.notna(row['封面']) else None
                summary = row['摘要'] if pd.notna(row['摘要']) else None
                create_time = None
                if pd.notna(row['创建时间']):
                    if isinstance(row['创建时间'], str):
                        create_time = datetime.strptime(row['创建时间'], '%Y-%m-%d %H:%M:%S')
                    else:
                        create_time = row['创建时间']

                publish_time = None
                if pd.notna(row['发布时间']):
                    if isinstance(row['发布时间'], str):
                        publish_time = datetime.strptime(row['发布时间'], '%Y-%m-%d %H:%M:%S')
                    else:
                        publish_time = row['发布时间']

                read_count = int(row['阅读']) if pd.notna(row['阅读']) else 0
                like_count = int(row['点赞']) if pd.notna(row['点赞']) else 0
                share_count = int(row['分享']) if pd.notna(row['分享']) else 0
                favorite_count = int(row['喜欢']) if pd.notna(row['喜欢']) else 0
                comment_count = int(row['留言']) if pd.notna(row['留言']) else 0
                author = row['作者'] if pd.notna(row['作者']) else None
                is_original = 0
                if pd.notna(row['是否原创']):
                    is_original_val = str(row['是否原创']).strip()
                    if is_original_val == '原创':
                        is_original = 1
                article_type = row['文章类型'] if pd.notna(row['文章类型']) else None
                collection = row['所属合集'] if pd.notna(row['所属合集']) else None
                content = row['文章内容'] if pd.notna(row['文章内容']) else None

                # 检查必要字段
                if not url or not title:
                    print(f"警告: 第{row_count}行缺少必要字段(url或title)，跳过")
                    skip_count += 1
                    continue

                # 插入数据
                cursor.execute(insert_query, (
                    sys_id, account_name, url, title, cover_image, summary, create_time, publish_time,
                    read_count, like_count, share_count, favorite_count, comment_count,
                    author, is_original, article_type, collection, content
                ))
                success_count += 1

                if success_count % 100 == 0:
                    print(f"已处理 {success_count} 行数据...")

            except Exception as e:
                print(f"处理第{row_count}行时出错: {e}")
                skip_count += 1
                continue

        connection.commit()
        print(f"数据导入完成:")
        print(f"  总行数: {row_count}")
        print(f"  成功插入: {success_count} 条记录")
        print(f"  跳过: {skip_count} 条记录")

    except Exception as e:
        print(f"插入数据时出错: {e}")
        connection.rollback()
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()


def main():
    # 创建参数解析器
    parser = argparse.ArgumentParser(description='将XLSX文件数据导入MySQL数据库')
    parser.add_argument('--host', required=True, help='MySQL服务器地址')
    parser.add_argument('--database', required=True, help='数据库名称')
    parser.add_argument('--user', required=True, help='用户名')
    parser.add_argument('--password', required=True, help='密码')
    parser.add_argument('--port', type=int, default=3306, help='端口号 (默认: 3306)')
    parser.add_argument('--xlsx-file', required=False, help='XLSX文件路径')

    # 解析命令行参数
    args = parser.parse_args()
    root_path = os.path.dirname(os.path.abspath(__file__)) + "/db_dir/"
    args.xlsx_file = root_path + "五分钟学大数据.xlsx"

    #从文件名中解析出account_name
    account_name = os.path.basename(args.xlsx_file).split(".")[0]

    # 检查XLSX文件是否存在
    if not os.path.exists(args.xlsx_file):
        print(f"文件 {args.xlsx_file} 不存在")
        return

    # 创建数据库连接
    connection = create_connection(args.host, args.database, args.user, args.password, args.port)
    if not connection:
        return

    try:
        # 插入数据
        insert_data_from_xlsx(connection, args.xlsx_file, account_name)
        print("数据导入完成")
    except Exception as e:
        print(f"导入过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭数据库连接
        if connection.is_connected():
            connection.close()
            print("MySQL连接已关闭")


if __name__ == "__main__":
    main()
