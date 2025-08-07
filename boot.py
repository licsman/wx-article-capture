import os
import warnings
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# 忽略 urllib3 的 OpenSSL 警告
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL 1.1.1+")

def setup_driver_with_existing_profile():
    """
    使用现有Chrome用户配置文件启动浏览器，保持登录状态
    """
    chrome_options = Options()

    # 指定用户数据目录（根据你的实际路径修改）
    # macOS 路径示例
    user_data_dir = "/Users/houmengqi/Library/Application Support/Google/Chrome"
    # 或者使用相对路径
    # user_data_dir = "~/Library/Application Support/Google/Chrome"

    # Windows 路径示例（根据实际情况修改）
    # user_data_dir = "C:\\Users\\[你的用户名]\\AppData\\Local\\Google\\Chrome\\User Data"

    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    chrome_options.add_argument("--profile-directory=Default")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # 允许在root用户下运行（如果需要）
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    # 注意：使用现有配置文件时不能使用detach选项
    # chrome_options.add_experimental_option("detach", True)

    # 确保用户数据目录存在且有权限
    if not os.path.exists(user_data_dir):
        print(f"警告: 用户数据目录不存在: {user_data_dir}")
        return None

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        print(f"启动浏览器时出错: {e}")
        return None

def open_wechat_page(driver):
    """
    打开微信公众号页面
    """
    url = "https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit_v2&action=edit&isNew=1&type=77&createType=0&token=1847671307&lang=zh_CN&timestamp=1754523886623"
    driver.get(url)
    time.sleep(5)  # 等待页面加载
    return driver.page_source

def find_hyperlinks(driver):
    """
    查找页面中的超链接元素
    """
    # 查找所有带href属性的<a>标签
    links = driver.find_elements(By.XPATH, "//a[@href]")

    link_info = []
    for link in links:
        href = link.get_attribute("href")
        text = link.text.strip()
        link_info.append({
            'href': href,
            'text': text
        })

    return link_info

# 主程序执行
if __name__ == "__main__":
    # 步骤1: 使用现有浏览器配置启动
    driver = setup_driver_with_existing_profile()

    if driver:
        try:
            page_source = open_wechat_page(driver)
            print("页面源代码获取成功")
            print("页面标题:", driver.title)

            # 检查是否已登录（通过页面元素判断）
            if "登录" in driver.title or "login" in driver.current_url.lower():
                print("警告: 可能未登录，请检查用户数据目录路径是否正确")
            else:
                print("已成功复用登录状态")

            # 步骤2: 查找超链接元素
            hyperlinks = find_hyperlinks(driver)
            print(f"共找到 {len(hyperlinks)} 个超链接")

            # 显示部分链接信息
            for i, link in enumerate(hyperlinks[:10]):  # 显示前10个
                print(f"{i+1}. {link['text'][:50]} -> {link['href'][:100]}")

        except Exception as e:
            print(f"执行过程中出错: {e}")
        finally:
            # 可选：不关闭浏览器以保持会话
            # driver.quit()
            pass
    else:
        print("无法启动浏览器")
