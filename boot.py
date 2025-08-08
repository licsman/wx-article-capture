import sys
import time
from time import sleep
import re
import os
import json
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchWindowException, WebDriverException, NoSuchElementException


def connect_to_existing_chrome():
    """连接到已经打开的Chrome浏览器"""
    chrome_options = Options()
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    try:
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(f"连接到浏览器时出错: {e}")
        return None


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


def extract_article_title(page_source):
    """
    从页面源码中提取文章标题
    """
    # 使用正则表达式匹配<meta property="og:title" content="..." />中的标题
    title_pattern = r'<meta\s+property="og:title"\s+content="([^"]+)"\s*/?>'
    match = re.search(title_pattern, page_source, re.IGNORECASE)

    if match:
        return match.group(1)
    else:
        # 备用方案：尝试从<title>标签获取
        title_pattern = r'<title>(.*?)</title>'
        match = re.search(title_pattern, page_source, re.IGNORECASE)
        if match:
            return match.group(1)

    return "未命名文章"


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


def get_article_links_from_page(driver):
    """
    从当前页面获取微信文章链接

    Args:
        driver: WebDriver实例

    Returns:
        list: 微信文章链接列表
    """
    links = driver.find_elements(By.XPATH, "//a[@href]")
    article_links = []

    for link in links:
        href = link.get_attribute("href")
        if href and href.startswith("https://mp.weixin.qq.com/s"):
            article_links.append(href)

    return article_links


def load_handled_links():
    """
    从文件中加载已处理的链接

    Returns:
        set: 已处理的链接集合
    """
    handled_links = set()
    if os.path.exists("handled_links.txt"):
        try:
            with open("handled_links.txt", "r", encoding="utf-8") as f:
                for line in f:
                    link = line.strip()
                    if link:
                        handled_links.add(link)
            print(f"已加载 {len(handled_links)} 个已处理的链接")
        except Exception as e:
            print(f"读取已处理链接文件时出错: {e}")
    return handled_links


def save_handled_link(link):
    """
    将链接保存到已处理链接文件中

    Args:
        link (str): 要保存的链接
    """
    try:
        with open("handled_links.txt", "a", encoding="utf-8") as f:
            f.write(link + "\n")
    except Exception as e:
        print(f"保存链接时出错: {e}")


def collect_all_article_links(driver):
    """
    收集所有页面中的微信文章链接（包括翻页）

    Args:
        driver: WebDriver实例

    Returns:
        list: 所有不重复的微信文章链接
    """

    # 加载已处理的链接
    handled_links = load_handled_links()

    all_links = set()  # 使用集合自动去重
    page_number = 1

    while True:
        print(f"正在处理第 {page_number} 页...")

        # 获取当前页面的链接
        current_page_links = get_article_links_from_page(driver)
        print(f"第 {page_number} 页找到 {len(current_page_links)} 个链接")

        # 添加到集合中（自动去重），并保存新链接
        new_links_count = 0
        for link in current_page_links:
            if link not in handled_links:
                all_links.add(link)
                handled_links.add(link)
                save_handled_link(link)
                new_links_count += 1
                print(f"  添加新链接: {link}")
            else:
                print(f"  跳过已处理链接: {link}")

        print(f"第 {page_number} 页新增 {new_links_count} 个链接")

        # 查找"下一页"按钮
        try:
            next_button = driver.find_element(By.XPATH,
                                              '//a[@class="weui-desktop-btn weui-desktop-btn_default weui-desktop-btn_mini" and text()="下一页"]')

            # 检查按钮是否可用（不是disabled状态）
            if next_button.is_enabled():
                print("点击下一页按钮...")
                next_button.click()

                # 随机等待几秒钟，模拟人工操作
                wait_time = random.randint(2, 5)
                print(f"等待 {wait_time} 秒...")
                sleep(wait_time)

                page_number += 1
            else:
                print("下一页按钮不可用，已到达最后一页")
                break

        except NoSuchElementException:
            print("未找到下一页按钮，已到达最后一页")
            break
        except Exception as e:
            print(f"点击下一页时出错: {e}")
            break

    print(f"总共收集到 {len(all_links)} 个新文章链接")
    return list(all_links)


def main():
    save_path = os.path.join(os.getcwd(), "pdf_articles")

    # 确保保存路径存在
    os.makedirs(save_path, exist_ok=True)
    print(f"PDF将保存到: {save_path}")

    # 第一步：连接到现有的远程调试浏览器以获取链接
    print("正在连接到现有浏览器以获取文章链接...")
    driver = connect_to_existing_chrome()

    if not driver:
        print("无法连接到浏览器。请确保：")
        print("1. 完全关闭所有Chrome浏览器实例")
        print("2. 运行以下命令启动支持远程调试的Chrome：")
        print("/Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\")
        print("    --remote-debugging-port=9222 \\")
        print("    --user-data-dir=\"/Users/houmengqi/Library/Application Support/Google/Chrome_Remote\"")
        print("3. 在打开的浏览器中访问微信公众号并登录")
        return

    article_link_list = []

    try:
        print("已连接到现有浏览器窗口")
        print("当前页面标题:", driver.title)

        # 查找所有页面的微信文章链接
        print("正在收集所有页面的文章链接...")
        article_link_list = collect_all_article_links(driver)

        if len(article_link_list) == 0:
            print("没有找到新的微信文章链接")
            return

    except Exception as e:
        print(f"获取链接时出错: {e}")
        import traceback
        traceback.print_exc()
        return
    finally:
        # 不要关闭原始浏览器连接，用户可能还需要使用它
        pass

    # 第二步：创建新的浏览器实例用于PDF下载
    print("正在创建用于PDF下载的浏览器实例...")
    pdf_driver = create_chrome_for_pdf(save_path)

    if not pdf_driver:
        print("无法创建PDF浏览器实例")
        return

    try:
        print("开始下载文章...")
        successful_downloads = 0
        failed_downloads = 0

        for i, link in enumerate(article_link_list, 1):
            try:
                print(f"\n[{i}/{len(article_link_list)}] 正在处理: {link}")

                # 打开新标签页并访问文章链接
                pdf_driver.execute_script(f'window.open("{link}");')
                pdf_driver.switch_to.window(pdf_driver.window_handles[-1])

                # 等待页面加载
                sleep(10)

                # 提取文章标题作为文件名
                file_name = extract_article_title(pdf_driver.page_source)
                # 清理文件名中的非法字符
                file_name = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', file_name)[:100]  # 限制长度

                if not file_name or file_name == "未命名文章":
                    file_name = f"微信文章_{i}"

                print(f"文章标题: {file_name}")

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
    main()
