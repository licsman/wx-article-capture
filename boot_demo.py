import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
from time import sleep

if __name__ == '__main__':
    save_path = os.getcwd()  # 当前文件所在的文件夹路径
    chrome_options = Options()
    settings = {
    "recentDestinations": [{
        "id": "Save as PDF",
        "origin": "local",
        "account": ""
    }],
    "selectedDestinationId": "Save as PDF",
    "version": 2,  # 另存为pdf，1 是默认打印机
    "isHeaderFooterEnabled": False,  # 是否勾选页眉和页脚
    "isCssBackgroundEnabled": True,  # 是否勾选背景图形
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
    chrome_options.add_argument('--enable-print-browser')  # 这一行试了，可用可不用
    chrome_options.add_argument('--kiosk-printing')  # 静默打印，无需用户点击打印页面的确定按钮
    chrome_options.add_experimental_option('prefs', prefs)
    driver = webdriver.Chrome(options=chrome_options)

    url = "https://mp.weixin.qq.com/s/7vLy4wqCIwyAsVF_geNB0g"
    driver.get(url)
    # 1.自定义pdf文件名字
    # driver.execute_script(f'document.title="自定义文件名.pdf";window.print();')
    # 2.默认pdf文件名字
    driver.execute_script('window.print();')
    # sleep这一行非常关键，时间短了，导致pdf还未生成，浏览器就关闭了。
    # 如果html图片较多，保存的pdf文件较大，或者如果电脑配置不好，等待时间可以再设置长一点。
    sleep(5)