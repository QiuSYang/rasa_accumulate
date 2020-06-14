"""
# 将一些原始数据处理成rasa可以支持的NLU数据
"""
import os
import re
import logging
import argparse
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataConverters(object):
    def __init__(self):
        pass

    @classmethod
    def data_to_rasa_nlu_data(cls,
                              source_file,
                              source_label,
                              output_rasa_nlu):
        output_rasa_nlu_list = output_rasa_nlu.strip().split('/')
        output_rasa_nlu_dir = "/".join(output_rasa_nlu_list[:-1])
        if not os.path.isdir(output_rasa_nlu_dir):
            # 路径不存在，创建路径
            os.makedirs(output_rasa_nlu_dir)

        with open(source_file, mode='r', encoding='utf-8') as fp_file:
            source_file_contents = fp_file.readlines()
        with open(source_label, mode='r', encoding='utf-8') as fp_label:
            source_label_contents = fp_label.readlines()

        with open(output_rasa_nlu, mode='w', encoding='utf-8') as fw_nlu:
            fw_nlu.write("{}\n".format("## intent:inform"))
            for index in range(len(source_file_contents)):
                data_lines = source_file_contents[index].strip().split(' ')
                label_lines = source_label_contents[index].strip().split(' ')
                if index == 250:
                    print(index)
                flag = None
                single_entity_name = str()
                entity_id_list = []
                temp_list = []
                for i, single_label in enumerate(label_lines):
                    if single_label is not 'O':
                        # temp = single_label[2:]
                        if single_label[2:] == flag and single_label[0] == 'I':
                            # 实体与头连接(寻找一个连续实体)
                            single_entity_name += data_lines[i]
                            temp_list.append(i)
                        else:
                            if flag is not None:
                                # 将每个实体索引列表加入行列表(因为类别实体可能是几个tokenize组成)
                                entity_id_list.append(temp_list)
                                # 对原始数据进行制作为rasa nlu识别的格式
                                new_entity_name = "[{}]({})".format(single_entity_name, flag)
                                data_lines[temp_list[0]] = new_entity_name
                                # 此方案还有其他错误
                                # if new_entity_name not in temp_list:
                                #     # data str 替换一次更新一次,
                                #     # 不进行重复替换，替换过一次就不在替换
                                #     data_str = data_str.replace(single_entity_name, new_entity_name)
                                # # 将所有要替换字符串加入列表，本想用正则匹配实现这个功能
                                # # 一旦data_str出现过new_entity_name模式就不在替换，
                                # # 但是经常会出现new_entity_name模式匹配不出来，所以改用list的形式
                                # temp_list.append(new_entity_name)

                                # 实体名更新，每一行可能存在多个实体名(前一个实体提取完成，进入下一个实体提取)
                                flag = single_label[2:]
                                single_entity_name = data_lines[i]
                                # temp list 置空, 下一个实体开始
                                temp_list = []
                                temp_list.append(i)
                            else:
                                # 第一次初始化变量（一般第一次出现label的时候）
                                temp_list = []
                                flag = single_label[2:]
                                single_entity_name = data_lines[i]
                                temp_list.append(i)

                # 每行的最后一个实体提取
                if flag is not None:
                    # 每一行最后一个实体加入每一行中
                    # 对原始数据进行制作为rasa nlu识别的格式
                    new_entity_name = "[{}]({})".format(single_entity_name, flag)
                    data_lines[temp_list[0]] = new_entity_name
                    # 下面这个方案还有很多特例存在bug
                    # if new_entity_name not in temp_list:
                    #     # data str 替换一次更新一次,
                    #     # 不进行重复替换，替换过一次就不在替换
                    #     data_str = data_str.replace(single_entity_name, new_entity_name)
                    # # 将所有要替换字符串加入列表，本想用正则匹配实现这个功能
                    # # 一旦data_str出现过new_entity_name模式就不在替换，
                    # # 但是经常会出现new_entity_name模式匹配不出来，所以改用list的形式
                    # temp_list.append(new_entity_name)

                del_indexes = []
                for single_entity_id in entity_id_list:
                    del_indexes.extend(single_entity_id[1:])

                data_valid_contents = [data_lines[i] for i in range(len(data_lines)) if i not in del_indexes]

                data_str = "".join(data_valid_contents)
                fw_nlu.write("{}\n".format(data_str))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-SF", "--source_file",
                        dest="source_file", type=str,
                        default="../data/source_data/nlu/source.txt",
                        help="source data file path.")
    parser.add_argument("-SL", "--source_label",
                        dest="source_label", type=str,
                        default="../data/source_data/nlu/target.txt",
                        help="source data label file path.")
    parser.add_argument("-OUTRASANLU", "--out_rasa_nlu",
                        dest="out_rasa_nlu", type=str,
                        default="../data/train_data/nlu/nlu.md",
                        help="output rasa nlu format data path.")
    args = parser.parse_args()

    DataConverters.data_to_rasa_nlu_data(args.source_file,
                                         args.source_label,
                                         args.out_rasa_nlu)
    pass
