"""
# 推理模块
"""
import os
import json
import argparse
import logging
import asyncio
from rasa.utils.endpoints import EndpointConfig
from tool.self_agent import SelfAgent

_logger = logging.getLogger(__name__)


class RasaInferenceTrial(object):
    def __init__(self, model_path='./models'):
        self.model_path = model_path
        self.agent = None

    def load_model(self):
        action_endpoint = EndpointConfig(url="http://localhost:5055/webhook")
        self.agent = SelfAgent.load(self.model_path, action_endpoint=action_endpoint)

    async def inference(self, nlu_info, dialogue_id=None):
        """
        :param nlu_info: dict 类型的数据
        :param dialogue_id: 对话ID
        :return:
        """

        responses = await self.agent.handle_text(nlu_info=nlu_info, sender_id=dialogue_id)

        return responses


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--modelSavePath", dest="modelSavePath",
                        default="./models",
                        type=str, help="model保存路径.")
    args = parser.parse_args()

    # 启动actions服务
    # os.system('start /b rasa run actions')

    pt = RasaInferenceTrial(model_path=args.modelSavePath)
    _logger.info('load rasa core model.')
    pt.load_model()

    _logger.info('continuous loading data prediction.')
    loop = asyncio.get_event_loop()
    index = 1
    dialogue_id = "dialogue_{}".format(str(index))
    nlu_info = {"intent": None, "entities": []}
    while True:
        # 开始每轮对话，第一轮NLU输入为空，获取开头语“utter_ask_own_name”
        print("User response: {}".format(nlu_info))
        responses = loop.run_until_complete(pt.inference(nlu_info, dialogue_id=dialogue_id))
        print("Bot response: {}".format(responses))
        for response in responses:
            if 'text' in response.keys():
                print("\t{}".format(response.get('text')))

        # msg输入格式：{"intent": {"name": "inform", "confidence": 1.0},
        #               "entities": [{"entity": "name", “start”: 2, “end”: 5, “value”: “孙悟空”}]}
        msg = input().strip()
        if msg == 'stop':
            break
        elif not msg:
            break
        elif msg == 'restart':
            index += 1
            dialogue_id = "dialogue_{}".format(str(index))
            nlu_info = {"intent": None, "entities": []}
            msg = input().strip()

        # 解析输入的字符串变为Dict
        input_dict = json.loads(msg)
        nlu_info['intent'] = input_dict.get('intent')
        if input_dict.get('entities'):
            nlu_info['entities'] = input_dict.get('entities')
        else:
            # 缺少'entities'字段，将其赋值为[](空列表)
            nlu_info['entities'] = []

