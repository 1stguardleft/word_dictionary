import os
import re
import logging
import MeCab

import sqlite3
import contextlib

import csv
import json

import requests
import xml.etree.ElementTree as ET

from typing import get_type_hints

from config import Configuration as cf

def init() -> str:
    'Step 1.1. 용어사전을 저장하기 위한 DB 세팅'
    db_url = os.path.join(cf.config['DATABASE']['database_dir'], cf.config['DATABASE']['database_name'])
    with contextlib.closing(sqlite3.connect(db_url)) as conn: # auto-closes
        with conn: # auto-commits
            with contextlib.closing(conn.cursor()) as cursor: # auto-closes
                cursor.execute(
                    '''
                    CREATE TABLE IF NOT EXISTS SOURCE (
                        SOURCE_KEY INTEGER PRIMARY KEY,
                        DATA_SOURCE TEXT NOT NULL,
                        COLUMN_NAME TEXT NOT NULL,
                        REFINED_COLUMN_NAME TEXT NULL,
                        TABLE_NAME TEXT NOT NULL
                    );
                    '''
                )

                cursor.execute(
                    '''
                    CREATE TABLE IF NOT EXISTS SEPERATION (
                        SOURCE_KEY INTEGER,
                        SEPERATION_NUMBER INTEGER,
                        SEPERATION_CODE TEXT NOT NULL,
                        TERM_NAME TEXT NOT NULL,
                        PRIMARY KEY (SOURCE_KEY, SEPERATION_NUMBER)
                    );
                    '''                    
                )

                cursor.execute(
                    '''
                    CREATE TABLE IF NOT EXISTS TERM (
                        SOURCE_KEY INTEGER,
                        SEPERATION_NUMBER INTEGER,
                        TERM_NAME TEXT NOT NULL,
                        TERM_MEAN TEXT NOT NULL,
                        TERM_ENG_NAME TEXT NULL,
                        ABBR_TERM_NAME TEXT NULL,
                        PRIMARY KEY (SOURCE_KEY, SEPERATION_NUMBER)
                    );
                    '''
                )
    return 0

def seperate_terms() -> int:
    'Step 2.1 Data 파일을 오픈'
    data_file_path = os.path.join(cf.config['DATA']['datafile_dir'], cf.config['DATA']['datafile_name'])
    db_url = os.path.join(cf.config['DATABASE']['database_dir'], cf.config['DATABASE']['database_name'])

    mecab = MeCab.Tagger()

    with open(data_file_path, encoding='UTF-8') as csvfile:
        reader = csv.reader(csvfile)
        with contextlib.closing(sqlite3.connect(db_url)) as conn: # auto-closes
            with conn: # auto-commits
                with contextlib.closing(conn.cursor()) as cursor: # auto-closes
                    for idx, row in enumerate(reader):
                        'Step 2.2.1 사용자 정의 정제 함수'
                        column : str = _remove_unnecessary_characters(row[3]) 
                        'Step 2.2.2 특수문자를 치환, 치환보다는 없애는 방향으로 구현'
                        column = _remove_special_characters(column)

                        'Step 2.3 Source 테이블에 데이터 저장'
                        cursor.execute(
                            '''
                            INSERT OR IGNORE INTO SOURCE VALUES (?, ?, ?, ?, ?)
                            ''', (row[0], row[1], row[3], column, row[2])
                        )
                        'Step 2.3.1 개별 단위로 commit 진행'
                        conn.commit()

                        'Step 2.4 mecab을 이용, 형태소로 나눔'
                        out = mecab.parse(column)

                        results = out.replace("\t", ",").replace("EOS", "").split("\n")

                        for idx, result_str in enumerate(results):
                            result = result_str.split(",")

                            if  len(result) >= 9:
                                'Step 2.5 SEPERATION 테이블에 데이터 저장'
                                cursor.execute(
                                    '''
                                    INSERT OR IGNORE INTO SEPERATION (SOURCE_KEY, SEPERATION_NUMBER, SEPERATION_CODE, TERM_NAME) VALUES (?, ?, ?, ?)
                                    ''', (row[0], idx, result[1], result[0])
                                )
                                'Step 2.5.1 개별 단위로 commit 진행'
                                conn.commit()
    return 0

def _remove_unnecessary_characters(input: str) -> str:
    pattern = r'\([^)]*\)'
    return re.sub(pattern=pattern, repl='', string= input)

def _remove_special_characters(input: str) -> str:
    return re.sub(r"[^\uAC00-\uD7A30-9a-zA-Z]", "", input)

def _remove_special_characters_without_space(input: str) -> str:
    return re.sub(r"[^\uAC00-\uD7A30-9a-zA-Z\s]", "", input)

def translate_terms_to_eng() -> int:
    db_url = os.path.join(cf.config['DATABASE']['database_dir'], cf.config['DATABASE']['database_name'])

    with contextlib.closing(sqlite3.connect(db_url)) as conn: # auto-closes
        with conn: # auto-commits
            with contextlib.closing(conn.cursor()) as cursor: # auto-closes   
                cursor.execute(
                    '''
                    SELECT SOURCE_KEY
                         , SEPERATION_NUMBER
                         , TERM_NAME
                      FROM SEPERATION
                     WHERE SEPERATION_CODE IN ('NNG', 'NNP', 'NNB')
                    '''
                )

                rows = cursor.fetchall()

                for row in rows:
                    headers = {'Content-Type': 'application/json', 'charset': 'UTF-8', 'Accept': '*/*'}
                    url='https://krdict.korean.go.kr/api/search?key=3D9E610A7AC48BAEF5E84B9DDB56FF63&q=%s&advanced=y&method=exact&translated=y&trans_lang=1' %  row[2]
                    response = requests.get(url, headers=headers)
                
                    root_element = ET.ElementTree(ET.fromstring(response.text.replace('\t', '').replace('\n', '')))
                    iter_element = root_element.iter(tag="sense")
                
                    definition : str
                    trans_word : str
                    
                    # 여러 개의 사전적 정의가 존재시 최초의 정의만을 취함.
                    for element in iter_element:
                        definition = element.find("definition").text # name태그 값을 저장합니다
                        trans_word = _remove_special_characters_without_space(element.find("translation").find("trans_word").text.split(";")[0])
                        break

                    cursor.execute(
                        '''
                        INSERT OR IGNORE INTO TERM (SOURCE_KEY, SEPERATION_NUMBER, TERM_NAME, TERM_MEAN, TERM_ENG_NAME) VALUES (?, ?, ?, ?, ?)
                        ''', (row[0], row[1], row[2], definition, trans_word.upper())
                    )

                    conn.commit()
    return 0

def abbreviate_terms() -> int:
    db_url = os.path.join(cf.config['DATABASE']['database_dir'], cf.config['DATABASE']['database_name'])

    with contextlib.closing(sqlite3.connect(db_url)) as conn: # auto-closes
        with conn: # auto-commits
            with contextlib.closing(conn.cursor()) as cursor: # auto-closes   
                cursor.execute(
                    '''
                    SELECT SOURCE_KEY
                         , SEPERATION_NUMBER
                         , TERM_ENG_NAME
                      FROM TERM
                    '''
                )

                rows = cursor.fetchall()

                for row in rows:
                    headers = {'Content-Type': 'application/json', 'charset': 'UTF-8', 'Accept': '*/*'}
                    url='https://wordic.loeaf.com/wordic-api/eng/%s' %  row[2]
                    response = requests.get(url, headers=headers)

                    res_dict = json.loads(response.text)
                    abbr_term : str = res_dict['result'][0]['text']

                    cursor.execute(
                        '''
                        UPDATE TERM SET ABBR_TERM_NAME = ? WHERE SOURCE_KEY = ? AND SEPERATION_NUMBER = ?;
                        ''', (abbr_term, row[0], row[1])
                    )

                    conn.commit()
    return 0

if __name__ == '__main__':
    init()
    seperate_terms()
    translate_terms_to_eng()
    abbreviate_terms()