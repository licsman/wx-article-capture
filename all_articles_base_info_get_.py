import sys
from time import sleep
import random
import csv
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchWindowException, WebDriverException, NoSuchElementException, \
    ElementNotInteractableException


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


def save_articles_to_csv(articles, account_name=""):
    """
    将文章信息保存到CSV文件中

    Args:
        articles (list): 文章信息列表
        account_name (str): 账号名称
    """
    if not articles:
        print("没有文章需要保存")
        return

    try:
        with open(filename, 'w', encoding='utf-8-sig', newline='') as csvfile:
            # 添加账号名称列到字段名，以及is_free字段
            fieldnames = ['account_name', 'title', 'link', 'release_date', 'is_free', 'collect_time']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # 写入表头
            writer.writeheader()

            # 写入数据
            for article in articles:
                # 为每篇文章添加账号名称
                article_with_account = {
                    'account_name': account_name,
                    'title': article['title'],
                    'link': article['link'],
                    'release_date': article['release_date'],
                    'is_free': article['is_free'],  # 1代表免费，0代表付费
                    'collect_time': article['collect_time']
                }
                writer.writerow(article_with_account)

        print(f"文章信息已保存到文件: {filename}")
        print(f"共保存 {len(articles)} 篇文章")
        if account_name:
            print(f"账号名称: {account_name}")

    except Exception as e:
        print(f"保存CSV文件时出错: {e}")


def get_article_info_from_page(driver):
    """
    从当前页面获取微信文章信息（标题、链接、发布日期、是否付费）

    Args:
        driver: WebDriver实例

    Returns:
        list: 包含文章信息字典的列表 [{'title': '', 'link': '', 'date': '', 'is_free': 1/0}, ...]
    """
    articles = []

    try:
        # 尝试多种XPath来查找文章项，提高兼容性
        article_items = []

        # 方法1: 原始XPath
        try:
            article_items = driver.find_elements(By.XPATH, '//label[@class="inner_link_article_item"]')
        except:
            pass

        # 如果方法1没有找到，尝试其他可能的XPath
        if not article_items:
            try:
                article_items = driver.find_elements(By.XPATH, '//div[contains(@class, "inner_link_article_item")]')
            except:
                pass

        # 如果还是没有找到，尝试直接查找文章标题和日期元素
        if not article_items:
            try:
                # 尝试直接查找文章标题元素
                title_elements = driver.find_elements(By.XPATH, '//div[@class="inner_link_article_title"]')
                if title_elements:
                    print(f"通过标题元素找到 {len(title_elements)} 个文章")
                    # 对于每个标题元素，尝试查找对应的链接和日期
                    for title_elem in title_elements:
                        try:
                            # 获取标题
                            title_spans = title_elem.find_elements(By.XPATH, './span')
                            if len(title_spans) >= 2:
                                title = title_spans[1].text.strip()
                            else:
                                title = title_elem.text.strip()

                            # 获取父级容器来查找链接和日期
                            parent = title_elem.find_element(By.XPATH,
                                                             './ancestor::label | ./ancestor::div[contains(@class, "inner_link_article_item")]')

                            # 查找链接
                            link_elem = parent.find_element(By.XPATH,
                                                            './/div[@class="inner_link_article_date"]//a[@href]')
                            link = link_elem.get_attribute("href") if link_elem else ""

                            # 查找日期
                            date_elem = parent.find_element(By.XPATH,
                                                            './/div[@class="inner_link_article_date"]/span[1]')
                            release_date = date_elem.text.strip() if date_elem else ""

                            # 检查是否付费
                            is_free = 1  # 默认为免费
                            try:
                                # 查找"付费"标签
                                pay_tag = parent.find_elements(By.XPATH,
                                                               './/div[contains(@class, "weui-desktop-key-tag_pay")]')
                                if pay_tag:
                                    is_free = 0  # 找到付费标签，标记为付费
                            except:
                                pass

                            # 获取当前时间作为采集日期
                            collect_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            if link and link.startswith("https://mp.weixin.qq.com/s"):
                                article_info = {
                                    'title': title,
                                    'link': link,
                                    'release_date': release_date,
                                    'is_free': is_free,  # 1代表免费，0代表付费
                                    'collect_time': collect_time
                                }
                                articles.append(article_info)
                                print(
                                    f"  标题: {title}，链接: {link}，发布日期: {release_date}, 是否免费: {is_free}, 采集日期: {collect_time}")

                        except Exception as e:
                            print(f"处理文章元素时出错: {e}")
                            continue
            except Exception as e:
                print(f"通过标题元素查找文章时出错: {e}")

        # 如果通过文章项容器找到了元素
        if article_items:
            print(f"找到 {len(article_items)} 个文章项")

            for item in article_items:
                try:
                    # 提取文章标题
                    title_element = item.find_element(By.XPATH, './/div[@class="inner_link_article_title"]/span[2]')
                    title = title_element.text.strip() if title_element else ""

                    # 提取文章链接
                    link_element = item.find_element(By.XPATH, './/div[@class="inner_link_article_date"]//a[@href]')
                    link = link_element.get_attribute("href") if link_element else ""

                    # 提取发布日期
                    date_element = item.find_element(By.XPATH, './/div[@class="inner_link_article_date"]/span[1]')
                    release_date = date_element.text.strip() if date_element else ""

                    # 检查是否付费 (1代表免费，0代表付费)
                    is_free = 1  # 默认为免费
                    try:
                        # 查找"付费"标签
                        pay_tag_elements = item.find_elements(By.XPATH,
                                                              './/div[@class="inner_link_article_title"]//div[contains(@class, "weui-desktop-key-tag_pay") and text()="付费"]')
                        if pay_tag_elements:
                            is_free = 0  # 找到付费标签，标记为付费
                    except:
                        pass

                    # 获取当前时间作为采集日期
                    collect_time = datetime.now().strftime("%Y%m%d%H%M%S")
                    # 只有当链接以https://mp.weixin.qq.com/s开头时才添加
                    if link and link.startswith("https://mp.weixin.qq.com/s"):
                        article_info = {
                            'title': title,
                            'link': link,
                            'release_date': release_date,
                            'is_free': is_free,  # 1代表免费，0代表付费
                            'collect_time': collect_time
                        }
                        articles.append(article_info)
                        print(f"  标题: {title}，链接: {link}，发布日期: {release_date}, 是否免费: {is_free}, 采集日期: {collect_time}")
                        print("---------------------------------------------------------------------------")
                    else:
                        print(f"  跳过无效链接: {link}")

                except Exception as e:
                    print(f"处理单个文章项时出错: {e}")
                    # 尝试备用方法
                    try:
                        # 备用方法：直接获取文本内容
                        item_text = item.text
                        print(f"  文章项文本内容: {item_text[:100]}...")
                    except:
                        pass
                    continue

    except Exception as e:
        print(f"查找文章项时出错: {e}")

    if not articles:
        print("未找到任何文章，尝试备用方法...")
        # 备用方法：通过链接反向查找标题和日期
        try:
            links = get_article_links_from_page(driver)
            for link in links:
                # 对于每个链接，尝试在其附近查找标题和日期
                try:
                    link_elements = driver.find_elements(By.XPATH, f'//a[@href="{link}"]')
                    for link_elem in link_elements:
                        try:
                            # 查找父级容器
                            parent = link_elem.find_element(By.XPATH,
                                                            './ancestor::*[contains(@class, "article")] | ./ancestor::*[contains(@class, "item")]')
                            # 尝试从父级容器提取信息
                            parent_text = parent.text
                            print(f"  链接 {link} 的父级容器文本: {parent_text[:100]}...")
                        except:
                            pass
                except:
                    pass
        except Exception as e:
            print(f"备用方法也失败: {e}")

    return articles


def is_next_button_available(driver):
    """
    检查下一页按钮是否可用

    Args:
        driver: WebDriver实例

    Returns:
        tuple: (是否找到按钮, 按钮元素)
    """
    try:
        # 查找下一页按钮，支持多种可能的表达方式
        next_buttons = driver.find_elements(By.XPATH,
                                            '//a[@class="weui-desktop-btn weui-desktop-btn_default weui-desktop-btn_mini" and text()="下一页"] | //a[contains(text(), "下一页")]')

        for next_button in next_buttons:
            # 检查按钮是否存在且可用
            if next_button and next_button.is_enabled() and next_button.is_displayed():
                return True, next_button

        return False, None
    except Exception as e:
        print(f"检查下一页按钮时出错: {e}")
        return False, None


from datetime import datetime


def parse_release_date(date_str):
    """
    解析发布日期字符串

    Args:
        date_str (str): 日期字符串

    Returns:
        datetime: 解析后的日期对象，如果解析失败返回None
    """
    if not date_str:
        return None

    # 支持多种常见的日期格式
    date_formats = [
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%Y年%m月%d日',
        '%Y-%m-%d %H:%M',
        '%Y/%m/%d %H:%M'
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    print(f"无法解析日期格式: {date_str}")
    return None


def is_before_2020(date_str):
    """
    检查日期是否在2020年之前

    Args:
        date_str (str): 日期字符串

    Returns:
        bool: 如果日期在2020年之前返回True，否则返回False
    """
    parsed_date = parse_release_date(date_str)
    if parsed_date is None:
        return False

    cutoff_date = datetime(2020, 1, 1)
    return parsed_date < cutoff_date


def collect_all_article_links(driver):
    """
    收集所有页面中的微信文章链接（包括翻页）

    Args:
        driver: WebDriver实例

    Returns:
        list: 所有不重复的文章信息列表
    """

    all_articles = []  # 存储所有文章信息
    page_number = 1

    while True:
        print(f"正在处理第 {page_number} 页...")

        # 获取当前页面的文章信息
        current_page_articles = get_article_info_from_page(driver)
        print(f"第 {page_number} 页找到 {len(current_page_articles)} 个文章")

        # 添加到列表中，并检查日期
        new_articles_count = 0
        should_stop = False

        for article in current_page_articles:
            # 检查日期是否在2020年之前
            if is_before_2020(article['release_date']):
                print(f"发现2020年前的文章: {article['title']} ({article['release_date']})")
                print("停止采集，不再翻页")
                should_stop = True
                break  # 停止处理当前页的剩余文章

            # 添加符合条件的文章
            link = article['link']
            all_articles.append(article)
            new_articles_count += 1
            print(f"  添加新文章: {article['title']}")

        print(f"第 {page_number} 页新增 {new_articles_count} 个文章")

        # 如果需要停止，直接退出循环
        if should_stop:
            break

        # 检查是否还有下一页
        is_available, next_button = is_next_button_available(driver)

        if is_available and next_button:
            try:
                print("点击下一页按钮...")
                # 使用JavaScript点击，有时比直接click()更可靠
                driver.execute_script("arguments[0].click();", next_button)

                # 随机等待几秒钟，模拟人工操作
                wait_time = random.randint(2, 5)
                print(f"等待 {wait_time} 秒...")
                sleep(wait_time)

                page_number += 1
            except ElementNotInteractableException:
                print("下一页按钮不可交互，可能已到达最后一页")
                break
            except Exception as e:
                print(f"点击下一页时出错: {e}")
                break
        else:
            print("未找到可用的下一页按钮，已到达最后一页")
            break

    print(f"总共收集到 {len(all_articles)} 个新文章")
    return all_articles


if __name__ == '__main__':
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
        print("4. 退出此脚本")
        sys.exit(1)

    article_link_list = []
    # 生成保存本次所有文章链接的文件名：wx_links_YYYYMMDDHHMMSS.csv
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"wx_links_{timestamp}.csv"

    try:
        print("已连接到现有浏览器窗口")
        print("当前页面标题:", driver.title)

        # 打印更多页面信息用于调试
        print("页面URL:", driver.current_url)

        # 获取账号名称
        print("请输入当前账号名称，并以回车结束...")
        account_name = input()

        # 查找所有页面的微信文章链接
        print("正在收集所有页面的文章链接...")
        article_link_list = collect_all_article_links(driver)

        if len(article_link_list) == 0:
            print("没有找到新的微信文章链接")
        else:
            # 保存文章信息到CSV文件，包含账号名称
            print("正在保存文章信息到CSV文件...")
            save_articles_to_csv(article_link_list, account_name)

    except Exception as e:
        print(f"获取链接时出错: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # 不要关闭原始浏览器连接，用户可能还需要使用它
        pass