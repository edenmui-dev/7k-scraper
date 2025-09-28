# %%

import os
from collections import defaultdict
from multiprocessing import Pool
from opencc import OpenCC
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import datetime as dt
import json
import pandas as pd
import re
import time
from typing import Literal

def get_urls(webpage: str) -> list[str]:
    """
    function to retrieve the list of urls for the dedicated page of the characters
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(webpage)

    time.sleep(5)

    xpath = "/html/body/div/div[1]/div/main/div/div/main/div[1]/div[2]/div[2]/div[2]/div[2]/div[1]/div[2]"

    link_elements = driver.find_elements(By.XPATH, xpath + "//a")
    link_list = []
    for link_element in link_elements:
        url = link_element.get_attribute("href")
        if url:
            link_list.append(str(url))
        else:
            link_list.append("-")
    driver.quit()
    return link_list


def _convert_hans_to_hant(text:str) -> str:
    """
    Function to convert simplified chinese to traditional chinese
    """
    cc = OpenCC("s2t")
    converted_text = cc.convert(text)
    return converted_text


def process_url(url: str) -> dict:
    """
    funciton to process the retrieved urls
    """
    chrome_options = Options()
    # Optional: run headless if you do not want browser windows visible
    # options.add_argument('--headless')
    # Run headless mode if no GUI needed
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)

    def return_default():
        return ""

    extraction_map = defaultdict(return_default)

    extraction_map.update(
        {
            "char_name": "/html/body/div[1]/div[1]/div/main/div/div/div/div[2]/div/div/div/div/div/div/article/div[2]/div/div[1]/div/div/div/div/div[2]/div[1]/div[2]/div[1]/div/div",
            "char_type": "/html/body/div[1]/div[1]/div/main/div/div/div/div[2]/div/div/div/div/div/div/article/div[2]/div/div[1]/div/div/div/div/div[2]/div[1]/div[2]/div[2]/div/div[1]/div/div[2]/div/div",
            "char_rarity": "/html/body/div[1]/div[1]/div/main/div/div/div/div[2]/div/div/div/div/div/div/article/div[2]/div/div[1]/div/div/div/div/div[2]/div[1]/div[2]/div[2]/div/div[2]/div/div[2]/div/div",
            "s1a": "/html/body/div[1]/div[1]/div/main/div/div/div/div[2]/div/div/div/div/div/div/article/div[2]/div/div[1]/div/div/div[2]/div/div[2]/div/div[1]",
            "s1b": "/html/body/div[1]/div[1]/div/main/div/div/div/div[2]/div/div/div/div/div/div/article/div[2]/div/div[2]/div/div/div[2]/div/div[1]/div/div[1]",
            "s2a": "/html/body/div[1]/div[1]/div/main/div/div/div/div[2]/div/div/div/div/div/div/article/div[2]/div/div[1]/div/div/div[2]/div/div[2]/div/div[2]",
            "s2b": "/html/body/div[1]/div[1]/div/main/div/div/div/div[2]/div/div/div/div/div/div/article/div[2]/div/div[2]/div/div/div[2]/div/div[1]/div/div[2]",
            "s3a": "/html/body/div[1]/div[1]/div/main/div/div/div/div[2]/div/div/div/div/div/div/article/div[2]/div/div[1]/div/div/div[2]/div/div[2]/div/div[3]",
            "s3b": "/html/body/div[1]/div[1]/div/main/div/div/div/div[2]/div/div/div/div/div/div/article/div[2]/div/div[2]/div/div/div[2]/div/div[1]/div/div[3]",
            "s4a": "/html/body/div[1]/div[1]/div/main/div/div/div/div[2]/div/div/div/div/div/div/article/div[2]/div/div[1]/div/div/div[2]/div/div[2]/div/div[4]",
            "s4b": "/html/body/div[1]/div[1]/div/main/div/div/div/div[2]/div/div/div/div/div/div/article/div[2]/div/div[2]/div/div/div[2]/div/div[1]/div/div[4]",
            "ascent": "/html/body/div[1]/div[1]/div/main/div/div/div/div[2]/div/div/div/div/div/div/article/div[2]/div/div[3]/div/div/div/div/div[2]",
        }
    )

    char_name = ""

    try:
        for name, path in extraction_map.items():
            try:
                # element = driver.find_element(By.XPATH, path)
                text = (
                    driver.find_element(By.XPATH, path).text
                    if driver.find_element(By.XPATH, path)
                    else ""
                )
                text = _convert_hans_to_hant(text)
                char_name = text.split(" ")[0] if name == "char_name" else char_name
                extraction_map.update({name: text})
            except:
                extraction_map.update({name: " !!! error !!! "})

    finally:
        package = {
            char_name: {
                "scanned": dt.datetime.now().isoformat(),
                "url": url,
                "type": extraction_map["char_type"],
                "rarity": extraction_map["char_rarity"],
                "s1": extraction_map["s1a"] + extraction_map["s1b"],
                "s2": extraction_map["s2a"] + extraction_map["s2b"],
                "s3": extraction_map["s3a"] + extraction_map["s3b"],
                "s4": extraction_map["s4a"] + extraction_map["s4b"],
                "ascent": extraction_map["ascent"],
            }
        }
        driver.quit()
        print(f"{char_name} completed.")
        return package


def _file_name(name: str) -> str:
    """
    function to add a file-system-safe suffix to a given file name
    """
    time = dt.datetime.now().strftime("%Y%m%d_%H%M%S")

    name, ext = name.split(".")

    file_name = f"{name}_{time}.{ext}"

    return file_name


def _create_backup(raw_data: dict) -> str:
    """
    function to create a backup json of the raw data after the urls have been processed
    """
    file = _file_name("raw_data.json")

    with open(file, "x", encoding="utf-8") as output:

        output.write(json.dumps(raw_data))

    return file


def read_backup(path: str) -> pd.DataFrame:
    """
    function to read the raw data from a backup json file
    """
    with open(path, "r") as input:
        data = input.read()
        info = json.loads(data)
        table_raw_data = pd.DataFrame.from_dict(info).transpose()
        table_raw_data["char"] = table_raw_data.index

    return table_raw_data


def process_raw_data(table_raw_data: pd.DataFrame) -> list[str]:
    """
    process the raw data and put the processed data into their respective tables following the 3NF standard
    """
    def _process_column(column: pd.Series) -> pd.DataFrame:
        pat = re.compile('技能強化效果|技能强化效果')
        n1 = column.str.split(pat,expand=True)
        n2 = n1.iloc[:, 0].str.split("\n", expand=True)
        n3 = n1.iloc[:, 1]
        table_skills = pd.DataFrame()
        table_skills[["sname", "target", "desc"]] = n2.iloc[:, 0:3]
        table_skills["upgrade"] = n3

        return table_skills

    # table_skills
    table_skills = pd.DataFrame()
    for col in dict(table_raw_data[["s1", "s2", "s3", "s4"]]).keys():
        table_from_column = _process_column(table_raw_data[col])
        table_from_column['type'] = str(col)
        table_skills = pd.concat([table_skills,table_from_column],axis=0)

    table_skills["cooldown"] = table_skills["sname"].str.extract("冷[卻却]{1}：([0-9]*)$")
    table_skills["sname"] = table_skills["sname"].apply(lambda x: x.split("冷[却卻]{1}：")[0])

    # table_ascant
    table_ascent = pd.DataFrame()
    pat = re.compile("突破[0-9]{1,2}")
    table_ascent[
        [
            "-",
            "ascent 1",
            "ascent 2",
            "ascent 3",
            "ascent 4",
            "ascent 5",
            "ascent 6",
            "ascent 7",
            "ascent 8",
            "ascent 9",
            "ascent 10",
            "ascent 11",
            "ascent 12",
        ]
    ] = table_raw_data["ascent"].str.split(pat, expand=True)

    table_ascent.drop("-", axis=1, inplace=True)

    # table_char
    table_char = table_raw_data.drop(["s1", "s2", "s3", "s4", "ascent"], axis=1)

    table_names = []

    for name, table in dict(
        {
            "table_char": table_char,
            "table_ascent": table_ascent,
            "table_skills": table_skills,
        }
    ).items():
        table["char"] = table.index

        table["char"] = table["char"].str.split(" ", expand=True)[0]
        for col in table.columns:
            table[col] = (
                table[col].apply(_convert_hans_to_hant)
                if table[col].dtype == str
                else table[col]
            )
            pat = re.compile("（|）|^[ \\-\\n】]*")
            table[col] = table[col].apply(lambda x : re.sub(pat,"",x) if isinstance(x,str) else x)
        file = _file_name(f"{name}.csv")
        table.to_csv(file, index=False)
        
        table_names.append(file)

    return table_names


def get_backup_tables(typ:Literal['table','raw']) -> dict[str,pd.DataFrame]:

    if typ.lower() not in ['table','raw']  or not(isinstance(typ,str)) or typ is None:
        raise TypeError("```typ must be one of 'table' or 'raw'```")
    
    path = '/Users/emporius/Documents/My Coding Projects/7knights'
    file_list = [doc for doc in os.listdir(path) if doc.startswith(typ)]

    latest_file_date = max(file_list,key=os.path.getctime).split('_',2)[2]
    print(f"latest_file_date = {latest_file_date}")
    package = {}
    if typ.lower() == 'table':
        pat = re.compile("table_.*_" + latest_file_date)
        lst = [file for file in file_list if re.match(pat,file)]
        for doc in lst:
            with open(doc,'r') as content:
                frame = pd.read_csv(content, low_memory=False)
                frame.set_index('char',inplace=True)
                name = "_".join(doc.split('_')[0:2])
                package.update({name:frame})
    elif typ.lower() == 'raw':
        lst = [f"raw_data_{latest_file_date}"]
        for doc in lst:
            with open(doc,'r') as content:
                frame = pd.read_json(content,orient='index')
                package.update({'raw_data':frame})
    
    return package

def main():
    """
    main sequence
    """
    webpage = "https://www.gamekee.com/sevenknights/"
    optimized_cpu_count = 6

    link_list = get_urls(webpage)
    with Pool(processes=optimized_cpu_count) as pool:
        results = pool.map(process_url, link_list)

    raw_data = {}
    for result in results:
        raw_data.update(result)

    file = _create_backup(raw_data)

    back_up_raw_data = read_backup(file)

    process_raw_data(back_up_raw_data)


if __name__ == "__main__":
    main()
    
    table_dict = get_backup_tables('table')
    
    table_char = table_dict.get('table_char')
    table_skills = table_dict.get('table_skills')
    table_ascent = table_dict.get('table_ascent')
    
    raw_data_dict = get_backup_tables('raw')
    raw_data = raw_data_dict.get('raw_data')
# %%
