# -*- coding: utf-8 -*-
"""
# 获取数据库中的数据
"""

import os
import sys
import json
import re
import time
import logging
import math
import numpy as np
import pandas as pd
from pypinyin import lazy_pinyin

_logger = logging.getLogger(__name__)


class LoadDB(object):
    def __init__(self):
        pass

    @classmethod
    def load_db_info(cls, db_file_path):
        """获取CSV文件中的数据，并存储在dict字典中
        """
        try:
            # staff_data_frame = pd.read_excel(db_file_path)
            # keep_default_na参数：将nan替换为''
            data_frame = pd.read_csv(db_file_path, dtype=np.str, keep_default_na=False)
            indexes = data_frame.index
            columns = list(data_frame.columns)
            db_info = {'index': [], 'info': {}}
            id = 0
            for index in indexes:
                line_data_dict = {}
                for column in columns:
                    line_data_dict[column] = data_frame.loc[index, column]
                # columns[0]第0列代表姓名
                # name = data_frame.loc[index, columns[0]].decode('utf-8')
                # python2
                # name_pinyin = ''.join(lazy_pinyin(data_frame.loc[index, columns[0]].decode('utf-8'))).encode('utf-8')
                # python3
                name_pinyin = ''.join(lazy_pinyin(data_frame.loc[index, columns[0]]))
                if db_info.get('info').get(name_pinyin):
                    id += 1
                    name_pinyin += str('_' + str(id))
                    db_info['info'][name_pinyin] = line_data_dict
                else:
                    db_info['info'][name_pinyin] = line_data_dict
            # 获取所有info字段字典所有的索引
            db_info['index'] = list(db_info.get('info').keys())

            return db_info
        except IOError:
            raise Exception("pandas read the {} file error.".format(db_file_path))

    @classmethod
    def get_staff_same_name(cls, db_info, input_name):
        """获取所有重名的名字"""
        same_name_info = {}
        same_name_list = [name for name in db_info.get('index') if input_name == re.sub(r'[^A-Za-z]', '', name)]
        same_name_info['index'] = same_name_list
        data_info = {}
        for name in same_name_list:
            single_info = {}
            single_info['name'] = db_info.get('info').get(name).get('员工姓名')
            single_info['department'] = db_info.get('info').get(name).get('部门')
            data_info[name] = single_info

        same_name_info['info'] = data_info

        return same_name_info

    @classmethod
    def get_visitor_same_name(cls, db_info, input_name):
        """获取所有重名的名字"""
        same_name_info = {}
        same_name_list = [name for name in db_info.get('index') if input_name == re.sub(r'[^A-Za-z]', '', name)]
        same_name_info['index'] = same_name_list
        data_info = {}
        for name in same_name_list:
            single_info = {}
            single_info['name'] = db_info.get('info').get(name).get('访客姓名')
            # single_info['department'] = db_info.get('info').get(name).get('部门')
            data_info[name] = single_info

        same_name_info['info'] = data_info

        return same_name_info


if __name__ == "__main__":
    staff_name_pinyin = ''.join(lazy_pinyin('姚明'))
    staff_path = '..\\data\\database\\staff.csv'
    visitor_path = '..\\data\\database\\visitor.csv'
    staff_info = LoadDB.load_db_info(staff_path)
    if staff_info.get('info').get(staff_name_pinyin).get('数字密码'):
        print(staff_info.get('info').get(staff_name_pinyin).get('数字密码'))
    else:
        print('数字密码为空.')
    visitor_info = LoadDB.load_db_info(visitor_path)

    print(LoadDB.get_staff_same_name(staff_info, staff_name_pinyin)['info'][staff_name_pinyin]['department'])
