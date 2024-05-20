import os
import re
import logging
import MeCab

import sqlite3
import contextlib

import requests

from config import Configuration as cf

def init() -> int:
    'Step 1.1. SAP 용어를 저장하기 위한 DB 세팅'
    db_url = os.path.join(cf.config['DATABASE']['database_dir'], cf.config['DATABASE']['database_name'])
    with contextlib.closing(sqlite3.connect(db_url)) as conn: # auto-closes
        with conn: # auto-commits
            with contextlib.closing(conn.cursor()) as cursor: # auto-closes
                cursor.execute(
                    '''
                    CREATE TABLE IF NOT EXISTS SAP_TERM (
                        ID TEXT NOT NULL,
                        NUMBER INTEGER NOT NULL,
                        TYPE TEXT NOT NULL,
                        NAME TEXT NOT NULL,
                        DESCRIPTION TEXT NULL,
                        RELATED_ELEMENT TEXT NULL,
                        DATA_TYPE TEXT,
                        LENGTH INTEGER,
                        PRIMARY KEY (ID, NUMBER)
                    );
                    '''
                )
    return 0

def scrap_sap_data_elements() -> int:

    headers = {'Content-Type': 'application/json', 'charset': 'UTF-8', 'Accept': '*/*'}
    url='https://www.sapdatasheet.org/abap/doma/index-a.html'
    response = requests.get(url, headers=headers)

    print(response.text)

    return 0

def scrap_sap_domains() -> int:
    return 0

if __name__ == '__main__':
    init()
    scrap_sap_data_elements()
    scrap_sap_domains()
    # translate_terms_to_eng()
    # abbreviate_terms()