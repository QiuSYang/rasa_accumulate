"""
# 训练和推理脚本
"""
import os
import logging
import argparse
import asyncio
from rasa.core import config
# from rasa.core.agent import Agent
from tool.self_agent import SelfAgent

_logger = logging.getLogger(__name__)


class RasaTrainTrial(object):
    def __init__(self, domainFile='configs/domain.yml',
                 configFile='configs/config.yml',
                 modelSavePath='models/core',
                 storiesFile='data/stories.md',
                 augmentationFactor=0):
        self.domainFile = domainFile
        self.configFile = configFile
        self.storiesFile = storiesFile
        self.augmentationFactor = augmentationFactor
        self.modelSavePath = modelSavePath
        if not os.path.isdir(self.modelSavePath):
            # 路径不存在，创建路径
            os.makedirs(self.modelSavePath)

    async def train(self):
        # agent = Agent(domain=self.domainFile, policies=config.load(self.configFile))
        agent = SelfAgent(domain=self.domainFile, policies=config.load(self.configFile))

        data = await agent.load_data(self.storiesFile,
                                     augmentation_factor=self.augmentationFactor)
        _logger.info("training model start.")
        agent.train(data)
        _logger.info('training model end.')
        _logger.info('save trained model.')
        agent.persist(self.modelSavePath)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--domainFile", dest="domainFile",
                        default='configs/domain.yml',
                        type=str, help="domain文件.")
    parser.add_argument("--configFile", dest="configFile",
                        default="configs/config.yml",
                        type=str, help="config文件.")
    parser.add_argument("--storiesFile", dest="storiesFile",
                        default="data/stories.md",
                        type=str, help="trial stories数据.")
    parser.add_argument("--modelSavePath", dest="modelSavePath",
                        default="models/core",
                        type=str, help="model保存路径.")
    parser.add_argument("--augmentationFactor", dest="augmentationFactor",
                        default=0,
                        type=int, help="augmentation factor.")

    args = parser.parse_args()

    pt = RasaTrainTrial(domainFile=args.domainFile, configFile=args.configFile,
                        storiesFile=args.storiesFile, modelSavePath=args.modelSavePath,
                        augmentationFactor=args.augmentationFactor)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(pt.train())
