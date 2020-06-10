# -----------
# rasa model inference
# -----------
import os 
import sys
import json
import logging
import urllib3
import asyncio
from rasa.nlu.model import Interpreter 
from rasa.core.interpreter import RegexInterpreter, INTENT_MESSAGE_PREFIX
from rasa.utils.endpoints import EndpointConfig
from custom_core.hci_agent import HciAgent
from tool.get_nlu_result_parse_server import GetNulResultAndParse
from tool.conversation_tracker_parse import TrackerParse

_logger = logging.getLogger(__name__)


def predict_nlu(model_path, text):
    interpreter = Interpreter.load(model_path)
    regex_interpreter = RegexInterpreter()

    if text.startswith(INTENT_MESSAGE_PREFIX):
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(regex_interpreter.parse(text))
    else:
        result = interpreter.parse(text)
    
    return result 


async def predict_core(agent, nlu_output_info, sender_id):
    input_nlu_dict = {"intent": nlu_output_info['intent'], "entities": nlu_output_info['entities']}

    responses = await agent.handle_text(nlu_info=input_nlu_dict,
                                        output_channel=None,
                                        sender_id=sender_id)

    ui_info = {'uiInfo': None}
    print("AI responses: {}".format(responses))
    for response in responses:
        if 'text' in response.keys():
            print("            {}".format(response['text']))
        if 'image' in response.keys():
            print("            {}".format(response['image']))
        if 'custom' in response.keys():
            uiInfo['uiInfo'] = response['custom']
    
    return ui_info


def get_nlu_result(input_content):
    output_parse_info = None
    text_msg = input_content
    input_msg_dict = {"user_id": 'YQS',
                      "topn": 3,
                      "asrScripts": [{"transcript": text_msg, "likelihood": 0.8}]}
    nlu_output_info = GetNulResultAndParse.get_nlu_result(input_msg_dict)
    output_parse_info = GetNulResultAndParse.result_parse(nlu_output_info)

    _logger.info('NLU content:{}'.format(output_parse_info))

    return output_parse_info


if __name__ == "__main__":
    text = "我是杨球松"
    output_parse_info = get_nlu_result(text)
    # 模型文件的解压路径
    core_model_path = 'models/core-20200610-160751.tar.gz'
    action_endpoint = EndpointConfig(url="http://localhost:5055/webhook")
    agent = HciAgent.load(core_model_path, action_endpoint=action_endpoint) 

    # 对话追踪对象
    dialogueTrackPt = TrackerParse(agent=agent)
    loop = asyncio.get_event_loop()
    print("AI response: {}".format("您好！人脸认证失败，语音助手为您服务，请问您是本公司员工吗？"))

    storyId = 1
    senderId = "story_id_{}".format(str(storyId))
    while True:
        msg = input("You response: ").strip()
        if msg == 'stop':
            break
        if not msg:
            break
        if msg == 'restart':
            storyId += 1
            senderId = "story_id_{}".format(str(storyId))
            print("AI response: {}".format("您好！人脸认证失败，语音助手为您服务，请问您是本公司员工吗？"))
            msg = input("You response: ").strip()

        # 获取NLU的结果
        nlu_output_info = get_nlu_result(msg)
        print('nlu output message: {}'.format(nlu_output_info))
        uiInfo = loop.run_until_complete(predict_core(agent, nlu_output_info, senderId))
        if uiInfo['uiInfo']:
            print(uiInfo)
        # 对话日志分析
        dialogueTrackPt.getLatestTracker(senderId=senderId)
