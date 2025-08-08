import argparse
import time
from time import sleep
import re
import os
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchWindowException, WebDriverException, NoSuchElementException
from download_articles_from_db import get_all_articles
from download_articles_from_db import create_connection

def create_chrome_for_pdf(save_path):
    """创建用于PDF打印的Chrome浏览器实例"""
    chrome_options = Options()
    settings = {
        "recentDestinations": [{
            "id": "Save as PDF",
            "origin": "local",
            "account": ""
        }],
        "selectedDestinationId": "Save as PDF",
        "version": 2,
        "isHeaderFooterEnabled": False,
        "isCssBackgroundEnabled": True,
        "mediaSize": {
            "height_microns": 297000,
            "name": "ISO_A4",
            "width_microns": 210000,
            "custom_display_name": "A4",
        },
    }
    prefs = {
        'printing.print_preview_sticky_settings.appState': json.dumps(settings),
        'savefile.default_directory': save_path,
    }
    chrome_options.add_argument('--enable-print-browser')
    chrome_options.add_argument('--kiosk-printing')  # 静默打印
    chrome_options.add_experimental_option('prefs', prefs)

    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"创建PDF浏览器实例时出错: {e}")
        return None


def wait_for_pdf_generation(save_path, file_name, timeout=60):
    """
    等待PDF文件生成

    Args:
        save_path (str): PDF保存路径
        file_name (str): 文件名
        timeout (int): 超时时间（秒）

    Returns:
        bool: 是否成功生成PDF
    """
    pdf_path = os.path.join(save_path, f"{file_name}.pdf")
    start_time = time.time()

    print('等待PDF生成...')
    while time.time() - start_time < timeout:
        if os.path.exists(pdf_path):
            size = os.path.getsize(pdf_path)
            # 确保文件不是空的并且已经完成写入
            if size > 0:
                # 再等待一小段时间确保文件完全写入
                sleep(2)
                final_size = os.path.getsize(pdf_path)
                if final_size == size:  # 文件大小稳定，说明写入完成
                    print(f"PDF生成完成: {pdf_path}")
                    return True
        sleep(1)

    print(f"PDF生成超时: {pdf_path}")
    return False


def main():
    save_path = os.path.join(os.getcwd(), "pdf_articles")

    # 确保保存路径存在
    os.makedirs(save_path, exist_ok=True)
    print(f"PDF将保存到: {save_path}")

    # 创建新的浏览器实例用于PDF下载
    print("正在创建用于PDF下载的浏览器实例...")
    pdf_driver = create_chrome_for_pdf(save_path)

    if not pdf_driver:
        print("无法创建PDF浏览器实例")
        return

    try:
        print("开始下载文章...")
        successful_downloads = 0
        failed_downloads = 0

        for i, article in enumerate(all_articles, 1):
            try:
                print(f"\n[{i}/{len(all_articles)}] 正在处理: {article}")

                # 打开新标签页并访问文章链接
                pdf_driver.execute_script(f'window.open("{article.link}");')
                pdf_driver.switch_to.window(pdf_driver.window_handles[-1])

                # 提取文章标题作为文件名
                title = article.title
                # 如果为0表示付费，1表示免费
                is_free = "免费" if article.is_free == 1 else "付费"
                id = article.id
                file_name = "[{}]-[{}]-{}".format(is_free, id, title)
                # 清理文件名中的非法字符
                file_name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', file_name)[:100]  # 限制长度

                if not file_name or file_name == "未命名文章":
                    file_name = f"微信文章_{i}"

                print(f"文章标题: {file_name}")

                # 等待页面加载并模拟滚动
                print(f"等待页面加载并模拟滚动以加载图片...")
                sleep(10)  # 初始等待

                # 模拟用户缓慢滚动到页面底部
                def scroll_to_bottom_slowly(driver, max_scrolls=30):
                    """
                    模拟用户缓慢滚动到页面底部，确保图片加载

                    Args:
                        driver: WebDriver实例
                        max_scrolls: 最大滚动次数，防止无限循环
                    """
                    scroll_count = 0
                    last_height = driver.execute_script("return document.body.scrollHeight")

                    while scroll_count < max_scrolls:
                        # 记录滚动前的位置
                        previous_position = driver.execute_script("return window.pageYOffset")

                        # 滚动一段距离
                        driver.execute_script("window.scrollBy(0, 500);")
                        # 等待一段时间让图片加载
                        sleep(2)

                        # 获取当前滚动位置和页面高度
                        current_position = driver.execute_script("return window.pageYOffset")
                        current_height = driver.execute_script("return document.body.scrollHeight")

                        scroll_count += 1
                        print(f"滚动进度: {scroll_count}/{max_scrolls}")

                        # 检查是否到达底部（允许一些误差）
                        if (current_height - (
                                current_position + driver.execute_script("return window.innerHeight"))) < 10:
                            print("已到达页面底部")
                            break

                        # 如果页面高度增加了，说明加载了新内容
                        if current_height > last_height:
                            last_height = current_height
                            print("检测到新内容加载，继续滚动...")
                            continue

                        # 如果滚动位置没有变化，可能已经到底部
                        if abs(current_position - previous_position) < 10:
                            print("滚动位置未变化，可能已到底部")
                            break

                    print(f"滚动完成，总共滚动 {scroll_count} 次")

                try:
                    scroll_to_bottom_slowly(pdf_driver)
                    print("页面滚动完成，图片应该已加载")
                except Exception as e:
                    print(f"滚动过程中出现错误: {e}")

                # 额外等待几秒确保所有图片加载完成
                sleep(5)

                # 执行打印操作
                print("正在生成PDF...")
                pdf_driver.execute_script(f'document.title="{file_name}.pdf"; window.print();')

                # 等待PDF生成
                if wait_for_pdf_generation(save_path, file_name):
                    successful_downloads += 1
                else:
                    failed_downloads += 1

            except NoSuchWindowException:
                print("浏览器窗口已关闭，尝试重新打开...")
                # 如果当前窗口关闭，切换到其他可用窗口或重新创建
                try:
                    if len(pdf_driver.window_handles) > 0:
                        pdf_driver.switch_to.window(pdf_driver.window_handles[0])
                    else:
                        # 重新创建浏览器实例
                        pdf_driver.quit()
                        pdf_driver = create_chrome_for_pdf(save_path)
                        if not pdf_driver:
                            print("无法重新创建浏览器实例")
                            break
                except:
                    print("无法恢复浏览器会话")
                    break

            except Exception as e:
                print(f"处理文章时出错: {e}")
                failed_downloads += 1
            finally:
                # 关闭当前标签页（如果不是最后一个）
                try:
                    if len(pdf_driver.window_handles) > 1:
                        pdf_driver.close()
                        # 切换到第一个标签页
                        pdf_driver.switch_to.window(pdf_driver.window_handles[0])
                    elif len(pdf_driver.window_handles) == 1:
                        # 如果只有一个标签页，重新打开一个空白页
                        pdf_driver.execute_script('window.open("about:blank");')
                        pdf_driver.close()
                        pdf_driver.switch_to.window(pdf_driver.window_handles[0])
                except:
                    pass

        print(f"\n下载完成!")
        print(f"成功: {successful_downloads} 篇文章")
        print(f"失败: {failed_downloads} 篇文章")

    except KeyboardInterrupt:
        print("\n用户中断下载过程")
    except Exception as e:
        print(f"下载过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            pdf_driver.quit()
            print("浏览器实例已关闭")
        except:
            pass


if __name__ == "__main__":
    # main()
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
    all_articles = get_all_articles(connection)
    main()

