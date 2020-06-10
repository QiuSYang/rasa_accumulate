# -*- coding: utf-8 -*-
"""
# 获取NLU结果并解析
"""
import os
import json
import logging
import urllib3
from sanic import Sanic, response

_logger = logging.getLogger(__name__)

app = Sanic(__name__)

# url = "http://10.128.2.33:9280/nlu_parser"
url = "http://10.128.12.215:9280/nlu_parser"
http = urllib3.PoolManager()


class GetNulResultAndParse(object):
    """获取NLU服务的结果并解析"""
    @classmethod
    def get_nlu_result(cls, message):
        headers = {'Content-Type': 'application/json'}
        r = http.request('POST', url=url, body=json.dumps(message).encode('utf-8'), headers=headers)
        nlu_output_dicts = json.loads(r.data.decode('utf-8'))

        return nlu_output_dicts

    @classmethod
    def result_parse(cls, nluInfo):
        no_intents = ['greet', 'confirm', 'deny', 'bye', 'thanks', 'chitchat']
        input_nlu_info = {'intent': None, 'entities': None, 'text': None}
        # 1> 获取高分语句
        min_score = -1.0
        # 获取意图的固定阈值，不再更新
        # min_confidence = -1.0
        for result in nluInfo['results']:
            if result['score'] > min_score:
                # 2> 获取置信度最高的intent
                intent_dict = {}
                if result['intents'][0]['name'] in no_intents:
                    intent_dict['name'] = result['intents'][0]['name']
                else:
                    # 将其他意图全部映射为staff_inform
                    intent_dict['name'] = 'staff_inform'
                intent_dict['confidence'] = result['intents'][0]['confidence']

                entities_list = []
                for entity_content in result['entities']:
                    if (entity_content['entity'] == 'e_name' and
                            len(entity_content['value']) <= 1):
                        # skip after
                        continue
                    temp_entity_dict = {}
                    temp_entity_dict['start'] = entity_content['start']
                    temp_entity_dict['end'] = entity_content['end']
                    temp_entity_dict['entity'] = entity_content['entity']
                    temp_entity_dict['value'] = entity_content['value']
                    temp_entity_dict['confidence'] = entity_content['confidence']
                    temp_entity_dict['extractor'] = entity_content['extractor']

                    entities_list.append(temp_entity_dict)

                input_nlu_info['intent'] = intent_dict
                input_nlu_info['entities'] = entities_list
                input_nlu_info['text'] = result['asrScript']['transcript']

                # 更新高分
                min_score = result['score']

        if not input_nlu_info['intent'] or not input_nlu_info['text']:
            return None
        else:
            return input_nlu_info

    @classmethod
    def resultParseBySingleIntent(cls, nluInfo):
        # input_nlu_info = {'intent': None, 'entities': None,
        #                   'intent_ranking': None, 'text': None}
        input_nlu_info = {'intent': None, 'entities': None, 'text': None}
        # 1> 获取高分语句
        min_score = -1.0
        # 获取意图的固定阈值，不再更新
        min_confidence = 0.5
        for result in nluInfo['results']:
            if result['score'] > min_score:
                # 2> 获取置信度最高的intent
                intent_dict = {}
                # intent_ranking_list = []
                # min_confidence = -1.0
                intentNameJoint = str()
                confidenceSum = 0.0
                index = 0
                useIntentList = []
                # tempResult = result['intents'][1:]
                for intent in result['intents'][1:]:
                    # temp_intent_dict = {}
                    # temp_intent_dict['name'] = intent['name']
                    # temp_intent_dict['confidence'] = intent['confidence']
                    # intent_ranking_list.append(temp_intent_dict)

                    if intent['confidence'] > min_confidence:
                        intentNameJoint += intent['name']
                        useIntentList.append(intent)
                        # 给联合意图之间添加一个+号
                        intentNameJoint += '+'
                        confidenceSum += intent['confidence']
                        index += 1

                entities_list = []
                for entity_content in result['entities']:
                    if (entity_content['entity'] == 'e_name' and
                            len(entity_content['value']) <= 1):
                        # skip after
                        continue
                    temp_entity_dict = {}
                    temp_entity_dict['start'] = entity_content['start']
                    temp_entity_dict['end'] = entity_content['end']
                    temp_entity_dict['entity'] = entity_content['entity']
                    temp_entity_dict['value'] = entity_content['value']
                    temp_entity_dict['confidence'] = entity_content['confidence']
                    temp_entity_dict['extractor'] = entity_content['extractor']

                    entities_list.append(temp_entity_dict)

                if not entities_list:
                    if len(useIntentList) == 1:
                        if useIntentList[0]['name'] in ['inform_digit_password', 'inform_digits',
                                                        'inform_work_id', 'inform_order',
                                                        'inform_department', 'inform_number',
                                                        'inform_phone_number_self', 'inform_phone_number_na',
                                                        'inform_name_self', 'inform_name_host', 'inform_name_na']:
                            # 映射为闲聊意图
                            intentNameJoint = 'chitchat'
                    elif len(useIntentList) > 1:
                        for singleIntent in useIntentList:
                            if singleIntent['name'] in ['inform_digit_password', 'inform_digits',
                                                        'inform_work_id', 'inform_order',
                                                        'inform_department', 'inform_number',
                                                        'inform_phone_number_self', 'inform_phone_number_na',
                                                        'inform_name_self', 'inform_name_host', 'inform_name_na']:
                                intentNameJoint = intentNameJoint.replace(singleIntent['name'] + '+', '')
                                index -= 1
                                confidenceSum = confidenceSum - singleIntent['confidence']

                # 所需NLU信息结构化组织
                # 组织输入intent数据，删除字符串开头和结尾‘+’号
                if intentNameJoint:
                    intent_dict['name'] = intentNameJoint.strip('+')
                    intent_dict['confidence'] = float(confidenceSum / float(index))
                elif result['intents'][1]['confidence'] >= 0.1:
                    intent_dict['name'] = result['intents'][1]['name']
                    intent_dict['confidence'] = 1.0  # result['intents'][1]['confidence']
                else:
                    intent_dict['name'] = 'chitchat'
                    intent_dict['confidence'] = 1.0
                    # intent_dict['name'] = result['intents'][0]['name']
                    # intent_dict['confidence'] = result['intents'][0]['confidence']

                input_nlu_info['intent'] = intent_dict
                input_nlu_info['entities'] = entities_list
                # input_nlu_info['intent_ranking'] = intent_ranking_list
                input_nlu_info['text'] = result['asrScript']['transcript']

                # 更新高分
                min_score = result['score']

        if not input_nlu_info['intent'] or not input_nlu_info['text']:
            return None
        else:
            return input_nlu_info


@app.route("model/parse", methods=['GET', 'POST'])
# @app.route("parse", methods=['GET', 'POST'])
def parse(request):
    input_body = request.json
    input_msg_dict = {"user_id": input_body['message_id'],
                      "topn": 3,
                      "asrScripts": [{"transcript": input_body['text'], "likelihood": 0.8}]}
    nlu_output_info = GetNulResultAndParse.get_nlu_result(input_msg_dict)
    output_parse_info = GetNulResultAndParse.result_parse(nlu_output_info)

    return response.json(output_parse_info)


if __name__ == "__main__":
    hostIp = '127.0.0.1'
    # hostIp = '0.0.0.0'
    portNum = 8080
    # portNum = 9180
    _logger.info('WSGI Server running on: {}:{}'.format(hostIp, portNum))
    app.run(host=hostIp, port=portNum)
