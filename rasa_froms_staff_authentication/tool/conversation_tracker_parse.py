# -*- coding: utf-8 -*-
"""
进行对话状态解析
"""
import os
import sys
import re
import asyncio
from rasa.nlu.model import Interpreter
from rasa.core.interpreter import RegexInterpreter, INTENT_MESSAGE_PREFIX
from rasa.utils.endpoints import EndpointConfig

from custom_core.hci_agent import HciAgent


class TrackerParse(object):
    def __init__(self, agent=None):
        self.interpreter = None
        self.regexInterpreter = None
        self.agent = agent
        self.loop = asyncio.get_event_loop()

    def nluModelLoad(self, nluModlePath):
        self.interpreter = Interpreter.load(nluModlePath)
        self.regexInterpreter = RegexInterpreter()

    def nluPredict(self, message):
        nluInfoDict = None
        if message.startswith(INTENT_MESSAGE_PREFIX):
            nluInfoDict = self.loop.run_until_complete(self.regexInterpreter.parse(message))
        else:
            nluInfoDict = self.interpreter.parse(message)
        return nluInfoDict

    def corePredict(self, nluInfoDict, senderId):
        responses, _ = self.loop.run_until_complete(self.agent.handle_text(nlu_info=nluInfoDict,
                                                                          sender_id=senderId,
                                                                          output_channel=None))
        # print("AI response message: {}".format(response))
        responsesData = str()
        for response in responses:
            if 'text' in response.keys():
                responsesData += response['text']

        return responsesData

    def coreModelLoad(self, coreModlePath):
        action_endpoint = EndpointConfig(url="http://localhost:5055/webhook")
        self.agent = HciAgent.load(coreModlePath, action_endpoint=action_endpoint)

    def trackerParse(self, senderId, fw):
        """提取对话状态内容
        Args:
            fw: 保存对话的文件
        """
        tracker = self.agent.tracker_store.get_or_create_tracker(senderId)

        # 解析对话管理状态
        index = 0
        for event in tracker.events:
            index += 1
            if index == 1:
                continue
            #name = event.type_name
            if event.type_name == 'action':
                actionName = event.action_name
                actionContent = "    - {}".format(actionName)
                fw.write("{}\n".format(actionContent))

            elif event.type_name == 'user':
                intent = event.intent['name']
                entities = {}
                for entity in event.entities:
                    entities[entity['entity']] = entity['value']
                if entities:
                    userContent = "* {}{}".format(intent, entities)
                else:
                    userContent = "* {}".format(intent)
                fw.write("{}\n".format(userContent))

            elif event.type_name == 'slot':
                slot = {}
                slot[event.key] = event.value
                slotContent = "    - slot{}".format(slot)
                fw.write("{}\n".format(slotContent))

            elif event.type_name == 'restart':
                # 标志一个对话story的结束
                break

        # 一个对话故事结束添加空行
        fw.write("\n")

    def getLatestTracker(self, senderId):
        # 获取最新的AI和用户信息（AI的表达，用户的表达，用户的意图）
        tracker = self.agent.tracker_store.get_or_create_tracker(senderId)
        # 每个类都应有get和set方法
        intent = tracker.latest_message.intent

        entities = {}
        for entity in tracker.latest_message.entities:
            entities[entity['entity']] = entity['value']

        return intent, entities

    def getTestData(self, testTextPath):
        """将文本数据转为格式化数据"""
        peopleTalkData = []

        # 使用python正则来解析文本
        storyPattern = '^ *## *'
        # botPattern = '^ *[bB][oO][tT] *[:：] *'
        userPattern = '^ *[yY][oO][uU] *[:：] *'
        element = {}
        storyId = None
        elementUserTalk = []
        index = 0
        with open(testTextPath, 'r', encoding='utf-8') as fp:
            for line in fp.readlines():
                line = line.rstrip()
                storyMatch = re.match(storyPattern, line)
                userMsgMatch = re.match(userPattern, line)

                if storyMatch:
                    element[storyId] = elementUserTalk
                    peopleTalkData.append(element)
                    element = {}
                    elementUserTalk = []
                    storyId = line[storyMatch.end():]
                    index += 1

                elif userMsgMatch:
                    elementUserTalk.append(line[userMsgMatch.end():])

            element[storyId] = elementUserTalk
            peopleTalkData.append(element)
            peopleTalkData = peopleTalkData[1:len(peopleTalkData)]

        print("story number is: {}".format(str(index)))
        return peopleTalkData

    def storiesActionCompare(self, testStories, predictStories):
        """对比测试集与预测的差异，求取精准度"""
        pass


if __name__ == "__main__":
    textPath = 'storiesTest.txt'
    storiesStorePath = 'rasaStore.md'
    pt = TrackerParse()
    # get data
    peopleTalkData = pt.getTestData(textPath)
    key = list(peopleTalkData[0].keys())

    # load model
    nluModelPath = 'models\\newIdea_1115\\nlu'
    coreModelPath = 'models\\newIdea_1115'
    pt.nluModelLoad(nluModelPath)
    pt.coreModelLoad(coreModelPath)

    with open(storiesStorePath, 'w', encoding='utf-8') as fw:
        index = 0
        for storyUserData in peopleTalkData:
            index += 1
            senderId = "story_id_{}".format(str(index))
            for userMessage in storyUserData[list(storyUserData.keys())[0]]:
                nluInfoDict = pt.nluPredict(userMessage)
                # 获取最新的对话的状态
                # pt.getLatestTracker(senderId)

                aiResponse = pt.corePredict(nluInfoDict, senderId)
                print("User message: {}".format(userMessage))
                print("Bot Message: {}".format(aiResponse))

                # 获取最新的对话的状态
                intent, entities = pt.getLatestTracker(senderId)

            # list(storyUserData.keys())[0] 是故事名称
            fw.write("## {}\n".format(list(storyUserData.keys())[0]))
            pt.trackerParse(senderId, fw)

