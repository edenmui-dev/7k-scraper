# %%

import os
import platform
import re
import shutil
import stat
import zipfile
from pathlib import Path
from urllib.request import urlopen
import json

from selenium import webdriver
from selenium.webdriver.common.by import By


def get_latest_chromedriver_url(endpoint):
    with urlopen(endpoint) as fp:
        info = json.load(fp.fp)
        url = list(d.get('url') for d in info.get('channels').get('Stable').get('downloads').get('chromedriver') if d.get('platform') == 'mac-arm64')[0]
        version = url.split('/')[4]
        return {'version':version,'url':url}

def _get_installed_chromedriver_version(chromedriver_dir):
    cmd = f"{chromedriver_dir}chromedriver --version"
    response = os.popen(cmd).read()
    if response == '':
        print('chromedriver not installed, now installing...')
        version = None
    if response != '':
        version = response.strip().replace('Google Chrome ',"")

    return version

def _download_and_replace_chromedriver(download_url, chromedriver_dir):
    chromedriver_dir = Path(chromedriver_dir)
    chromedriver_dir.mkdir(parents=True, exist_ok=True)
    zip_path = chromedriver_dir / "chromedriver.zip"
    print(f"Downloading ChromeDriver from {download_url}...")
    with urlopen(download_url) as response, open(zip_path, "wb") as out_file:
        shutil.copyfileobj(response, out_file)
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extract('chromedriver-mac-arm64/chromedriver',chromedriver_dir)
    driver_path = f'{chromedriver_dir}/chromedriver-mac-arm64/chromedriver'
    print(f"ChromeDriver updated at: {driver_path}")
    if platform.system() != "Windows":
        st = os.stat(driver_path)
        os.chmod(driver_path, st.st_mode | stat.S_IEXEC)


def update(endpoint, chromedriver_dir):

    installed_chromedriver_version = _get_installed_chromedriver_version(chromedriver_dir)

    if not installed_chromedriver_version:
        print("Could not detect installed Chrome version.")
    else:
        print(f"Installed Chrome version: {installed_chromedriver_version}")
    
    package = get_latest_chromedriver_url(endpoint)
    latest_version = package['version']
    latest_chromedriver_url = package['url']

    if latest_version == installed_chromedriver_version:
        pass
    else:
        _download_and_replace_chromedriver(latest_chromedriver_url, chromedriver_dir)

# %%
