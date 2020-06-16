"""
# 进行model inference test
"""
import os
import logging
import asyncio
from rasa.core.agent import Agent
from rasa.utils.endpoints import EndpointConfig

logger = logging.getLogger(__name__)


class RasaInference(object):
    def __init__(self,
                 model_path="models/20200611",
                 action_url="http://localhost:5055/webhook"):
        self.agent = Agent.load(model_path,
                                action_endpoint=EndpointConfig(url=action_url))

    async def nlu_inference(self, input_message):
        """ rasa nlu predict
        :param input_message: 支持文本输入和结构化数据输入
                            （结构化数据包括：/intent{entity content}）
        :return: parse_data
        """
        parse_data = await self.agent.parse_message_using_nlu_interpreter(message_data=input_message)

        return parse_data

    async def core_inference(self, input_message, sender_id):
        """
        :param input_message: 支持文本输入和结构化数据输入
                            （结构化数据包括：/intent{entity content}）
        :param sender_id: 对话ID
        :return: responses
        """
        responses = await self.agent.handle_text(text_message=input_message,
                                                 sender_id=sender_id)

        return responses


if __name__ == "__main__":
    model_path = "models/rasa_train/20200615"
    pt = RasaInference(model_path=model_path)

    loop = asyncio.get_event_loop()
    while True:
        input_text = input("please a text: ")
        if input_text is "stop":
            break
        parse_data = loop.run_until_complete(pt.nlu_inference(input_text))

        print("'{}' nlu parse is {}".format(input_text, parse_data))
