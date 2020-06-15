# -*- coding: utf-8 -*-
"""
# 训练NLU和core脚本
"""
import os
import logging
import asyncio
from rasa.nlu.train import train as train_nlu_model
from rasa.core.train import train as train_core_model

logger = logging.getLogger(__name__)


class RasaTrain(object):
    def __init__(self):
        pass

    @classmethod
    async def train_nlu(cls,
                        nlu_config,
                        nlu_data_path,
                        model_save_path):
        """ NLU model training
        :param nlu_config:
        :param nlu_data_path:
        :param model_save_path:
        :return:
        """
        if not os.path.isdir(model_save_path):
            # 路径不存在，创建路径
            os.makedirs(model_save_path)

        trainer, interpreter, persisted_path = await train_nlu_model(nlu_config=nlu_config,
                                                                     data=nlu_data_path,
                                                                     path=model_save_path)

        return trainer, interpreter, persisted_path

    @classmethod
    async def train_core(cls,
                         domain_file,
                         policy_config,
                         stories_data_path,
                         model_save_path):
        """core model training
        :param domain_file:
        :param policy_config:
        :param stories_data_path:
        :param model_save_path:
        :return:
        """
        if not os.path.isdir(model_save_path):
            # 路径不存在，创建路径
            os.makedirs(model_save_path)
        agent = await train_core_model(domain_file=domain_file,
                                       policy_config=policy_config,
                                       training_resource=stories_data_path,
                                       output_path=model_save_path)

        return agent


if __name__ == "__main__":
    nlu_config_file = "config.yml"
    nlu_data_path = "data/train_data/nlu"
    model_output_path = "models/rasa_train/20200615"

    loop = asyncio.get_event_loop()
    trainer, interpreter, persisted_path = loop.run_until_complete(
                                        RasaTrain.train_nlu(nlu_config=nlu_config_file,
                                                            nlu_data_path=nlu_data_path,
                                                            model_save_path=model_output_path))
