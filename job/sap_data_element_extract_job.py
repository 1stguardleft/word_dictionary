#
import os, sys
import sqlite3
import contextlib
import json

import requests
from bs4 import BeautifulSoup

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Configuration as cf

class SAPDataElementExtractJob():

    indexes_per_character = {}

    # New instance instantiation procedure 
    def __init__(self):
        'Step 1.1. 용어사전을 저장하기 위한 DB 세팅'
        db_url = os.path.join(cf.config['DATABASE']['database_dir'], cf.config['DATABASE']['database_name'])
        with contextlib.closing(sqlite3.connect(db_url)) as conn: # auto-closes
            with conn: # auto-commits
                with contextlib.closing(conn.cursor()) as cursor: # auto-closes
                    cursor.execute(
                        '''
                        CREATE TABLE IF NOT EXISTS SAP_DATA_ELEMENT (
                            DATE_ELEMENT_KEY TEXT PRIMARY KEY,
                            NAME TEXT NOT NULL,
                            DESCRIPTION TEXT NOT NULL,
                            DOMAIN TEXT NULL,
                            DATA_TYPE TEXT NOT NULL
                        );
                        '''
                    )
        'Step 1.1. 초기 페이지에서 인덱스별 전체 Pages 수 획득하여 메모리에 저장'
        headers = {'Content-Type': 'application/json', 'charset': 'UTF-8', 'Accept': '*/*'}
        url='https://' + cf.config['SAP']['sap_data_element_url']
        response = requests.get(url, headers=headers)

        soup = BeautifulSoup(response.text, "html.parser")
        count_per_char = soup.find_all("a", "page-link")

        idx = 'A'
        for n, count in enumerate(count_per_char):
            if n > 0:
                self.indexes_per_character[idx] = int(count['title'].split(' ')[-2])
                idx = chr(ord(idx) + 1)

    def execute(self) -> str:
        
        for key, val in self.indexes_per_character.items():
            for idx in range(val):
                # index-a-1.html
                html_name = 'index-%s-%s.html' % key.lower(), int(val)
                target_url = 'https://' + cf.config['SAP']['sap_data_element_url'] + '/' + html_name

                print(target_url)

                break
            break
        return '0'

if __name__ == '__main__':
    extractor = SAPDataElementExtractJob()
    extractor.execute()
