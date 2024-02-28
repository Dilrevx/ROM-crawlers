import os
import subprocess
from typing import List
import requests
import logging
import urllib.request
from bs4 import BeautifulSoup
import bs4.element
import json

FILEDIR = os.path.dirname(os.path.abspath(__file__))
CWD = os.path.normpath(os.path.join(FILEDIR, './../../'))


def initLogger(logDir):
    os.makedirs(logDir, exist_ok=True)
    logging.basicConfig(level=logging.INFO,
                        filename=os.path.join(logDir, 'google.log'),
                        encoding='utf-8',
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def parseTable(table: bs4.element.Tag) -> List[dict]:
    '''
    name: nickname for a version of img, the h2.id before table
    table: download table with 3 or 4 column 
    '''
    ret = []
    ret: List[dict]
    col2op = {"Version": lambda x: ret[-1].update({"Version": x.text.strip()}),
              "Flash": lambda x: None,
              "Download": lambda x: ret[-1].update({"Download": x.a["href"].strip()}),
              "SHA-256 Checksum": lambda x: ret[-1].update({"SHA-256 Checksum": x.text.strip()})}

    ths = tuple(map(lambda th: th.text, table.thead.find_all('th')))
    trs = table.find_all("tr")

    for tr in trs:
        ret.append({})
        for i, td in enumerate(tr.find_all("td")):
            th = ths[i]
            col2op[th](td)
        assert ret[-1]["Version"] and ret[-1]["Download"].endswith(
            ".zip"), "Page structure changed"

    return ret


def parseLinks(response: requests.Response):
    '''
    First parse the table into a JSON, store locally and download them
    '''
    JSONPath = os.path.join(CWD, 'json', 'google')
    os.makedirs(JSONPath, exist_ok=True)

    logging.info("Building soup and dumping json")
    soup = BeautifulSoup(response.text, 'html.parser')

    # Currently, each table have a h2 title
    h2s = soup.find_all('h2')
    _ = tuple(filter(lambda x: x.text.startswith('"'), h2s))

    assert len(_) == len(h2s) - 4, "page structure changed"
    h2s = _  # First 4 <h2> is text

    jsonTables = {}
    for i, h2 in enumerate(h2s):
        table = h2.find_next_sibling()
        assert table.name == 'table'

        parsedTable = parseTable(table)
        jsonTables[h2.text.strip()] = parsedTable

    with open(os.path.join(JSONPath, 'index.json'), 'w') as f:
        json.dump(jsonTables, f, indent=2)


def main():
    baseURL = 'https://developers.google.com/android/images'
    overrideProxy = {
        'http': 'http://localhost:7890',
        'https': 'http://localhost:7890'
    }

    # For clash, proxy https with http to change urllib3 behavior
    proxies = urllib.request.getproxies()
    if not proxies:
        proxies = overrideProxy
    elif proxies['https'].startswith('https'):
        proxies['https'] = proxies['http'].replace('https', 'http', 1)

    headers = {
        "Accept-Language": "en-US,en;q=0.9",
        "Cookie": "_ga_devsite=GA1.3.2552052132.1709034549; cookies_accepted=true; django_language=en; _ga=GA1.1.2011300747.1709034637; _ga_0587J3GZY5=GS1.1.1709034637.1.0.1709034637.0.0.0; devsite_wall_acks=nexus-image-tos; _ga_272J68FCRF=GS1.1.1709034637.1.1.1709034648.0.0.0",
    }

    rawPath = os.path.join(CWD, 'raw', 'google')
    os.makedirs(rawPath, exist_ok=True)

    logging.info("configures proxy, header, sending GET to google")
    response = requests.get(baseURL, proxies=proxies, headers=headers)
    with open(os.path.join(rawPath, 'index.html'), 'wb') as f:
        f.write(response.content)

    assert 'cheetah' in response.text,  "Links cannot parse, new cookie needed or frontend changed."

    parseLinks(response)

    logging.warning("Start downloading")

    subprocess.run(['python', os.path.join(
        FILEDIR, 'dlmgr.py')], cwd=CWD)


if __name__ == '__main__':
    initLogger(os.path.join(CWD, 'log', 'google'))
    main()
