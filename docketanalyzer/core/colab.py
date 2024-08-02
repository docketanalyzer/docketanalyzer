import os
import socket
import subprocess
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import docketanalyzer


def get_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def start_selenium_server(port):
    cmd = f"xvfb-run java -jar selenium-server-standalone.jar -port {port}"
    process = subprocess.Popen(cmd, shell=True)
    return process


def setup_selenium_in_colab():
    os.system('apt-get update')
    os.system('apt-get install -y xvfb chromium-chromedriver')
    os.system('cp /usr/lib/chromium-browser/chromedriver /usr/bin')
    os.system('pip install selenium pyvirtualdisplay')
    os.system('wget https://selenium-release.storage.googleapis.com/3.141/selenium-server-standalone-3.141.59.jar -O selenium-server-standalone.jar')

    from pyvirtualdisplay import Display

    try:
        display = Display(visible=0, size=(800, 600))
        display.start()
    except Exception as e:
        print(f"Warning: Could not start virtual display. Error: {e}")
        print("Continuing without virtual display...")

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    port = get_free_port()
    server_process = start_selenium_server(port)

    for _ in range(30):
        if is_port_in_use(port):
            break
        time.sleep(1)
    else:
        raise Exception("Selenium server didn't start in time")
    docketanalyzer.utils.SELENIUM_PORT = port


def setup_colab(skip_selenium=False):
    os.environ['DJANGO_ALLOW_ASYNC_UNSAFE'] = 'true'
    if not skip_selenium:
        setup_selenium_in_colab()
