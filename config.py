# -*- coding : utf-8 -*-

import os
import configparser

def _get_config(parser):
    return {s:dict(parser.items(s)) for s in parser.sections()}

class Configuration():
    """
    배치 구동시 필요한 설정에 대한 정보를 관리하는 클래스
    """
    this_file = __file__
    path = os.path.dirname(this_file)

    ini_file_path = os.path.join(path, 'config.ini')
    parser = configparser.RawConfigParser()
    parser.read(ini_file_path)

    config = _get_config(parser)
    