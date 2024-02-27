import logging
import os
import json
import subprocess
from typing import Dict, List

'''
cwd guaranteed to be the crawler directory
'''
CWD = os.getcwd()
ARIA_CMD = "aria2c -i {} -j 8"


def pickUpDlLink(dlList: List[Dict[str, str]]) -> List[Dict]:
    '''
    Maybe duplicate
    '''
    occuredVersion = set()
    lastOccuredEntry = {}

    ret = []
    for entry in dlList:
        version = entry["Version"]
        link = entry["Download"]

        version = version.split(" ")[0]
        if version not in occuredVersion:
            ret.append(lastOccuredEntry)
            ret.append(entry)

        occuredVersion.add(version)
        lastOccuredEntry = entry
    return ret[1:]


if __name__ == "__main__":
    # make a .zip list and leave it to aria2c
    JSONPath = os.path.join(CWD, 'json', 'google')
    downloadPath = os.path.join(CWD, 'download', 'google')
    logging.basicConfig(level=logging.INFO,
                        filename=os.path.join('log', 'google.log'),
                        encoding='utf-8',
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    def download(nameStr: str, dlList: List[Dict[str, str]]):
        name = nameStr.split('"')[1]
        assert name

        dlPath = os.path.join(downloadPath, name)
        os.makedirs(dlPath, exist_ok=True)

        entrys = pickUpDlLink(dlList)
        logging.info("pickup {} links for {}".format(len(entrys), name))

        os.makedirs(os.path.join(JSONPath, 'dlLink'), exist_ok=True)
        with open(os.path.join(JSONPath, 'dlLink', name + '.json'), 'w') as f:
            json.dump(entrys, f, indent=2)
        with open(os.path.join(dlPath, 'links'), 'w') as index:
            index.writelines(map(lambda x: x["Download"] + '\n', entrys))

        cmd = ARIA_CMD.format(os.path.join(dlPath, 'links'))
        logging.info("executing: " + cmd)
        subprocess.run(cmd, shell=True, cwd=dlPath)

    with open(os.path.join(JSONPath, 'index.json'), 'r') as f:
        data = json.load(f)
        for nameStr, dlList in data.items():
            download(nameStr, dlList)
