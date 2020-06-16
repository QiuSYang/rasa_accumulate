"""
# 自定义命名实体提取器(ner), 使用youdao kashgari库 + bert + crf 进行
"""
import logging
from typing import Any, Dict, List, Optional, Text

from rasa.nlu.extractors import EntityExtractor
from rasa.nlu.model import Metadata
from rasa.nlu.training_data import Message

import os
import math
import datetime
import shutil
import kashgari
from kashgari.embeddings import BERTEmbedding
import kashgari.tasks.labeling as labeling
from sklearn.model_selection import train_test_split
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau, TensorBoard

logger = logging.getLogger(__name__)


class CustomEntityExtractor(EntityExtractor):
    """默认使用bert word2vector, BiLSTM+CRF进行实体抽取"""
    provides = ["entities"]

    # 默认参数
    defaults = {
        "bert_model_path": None,
        "sequence_length": "auto",
        "layer_nums": 4,
        "trainable": False,
        "labeling_model": "BiLSTM_CRF_Model",
        "epochs": 10,
        "batch_size": 32,
        "validation_split": 0.2,
        "patience": 5,
        "factor": 0.5,  # factor of reduce learning late everytime
        "verbose": 1,
        "use_cudnn_cell": False
    }

    def __init__(self,
                 component_config=None,
                 model=None):
        super(CustomEntityExtractor, self).__init__(component_config)

        self.bert_model_path = self.component_config.get('bert_model_path')
        self.sequence_length = self.component_config.get('sequence_length')
        self.layer_nums = self.component_config.get('layer_nums')
        self.trainable = self.component_config.get('trainable')
        self.use_cudnn_cell = self.component_config.get('use_cudnn_cell')


        # 设置是否使用cudnn进行加速训练，True为加速训练，false反之
        # 训练使用cudnn加速，那么inference也只能使用cudnn加速
        kashgari.config.use_cudnn_cell = self.use_cudnn_cell

        self.labeling_model = self.component_config.get('labeling_model')

        # self.bert_embedding = BERTEmbedding(self.bert_model_path,
        #                                     task=kashgari.LABELING,
        #                                     layer_nums=self.layer_nums,
        #                                     trainable=self.trainable,
        #                                     sequence_length=self.sequence_length)
        self.bert_embedding = None

        self.model = model

    def train(self, training_data, cfg, **kwargs):
        """继承Component的训练函数，重构训练体"""
        labeling_model = eval("labeling." + self.labeling_model)

        epochs = self.component_config.get('epochs')
        batch_size = self.component_config.get('batch_size')
        validation_split = self.component_config.get('validation_split')
        patience = self.component_config.get('patience')
        # 训练学习率下降的改变因子
        factor = self.component_config.get('factor')
        verbose = self.component_config.get('verbose')

        # 获取训练数据
        filtered_entity_examples = self.filter_trainable_entities(training_data.training_examples)

        # 获取X Y
        X, Y = self._create_dataset(filtered_entity_examples)

        # 训练数据与验证数据分离
        train_x, validate_x, train_y, validate_y = train_test_split(X, Y, test_size=validation_split, random_state=100)

        # 128作为序列的基数
        sequence_length_base = self.component_config.get('sequence_length')
        self.sequence_length = math.ceil(self.sequence_length/sequence_length_base) * sequence_length_base

        self.bert_embedding = BERTEmbedding(self.bert_model_path,
                                            task=kashgari.LABELING,
                                            layer_nums=self.layer_nums,
                                            trainable=self.trainable,
                                            sequence_length=self.sequence_length)
        # load 模型结构
        self.model = labeling_model(self.bert_embedding)

        # 设置回调状态
        checkpoint = ModelCheckpoint(
            'entity_weights.h5',
            monitor='val_loss',
            save_best_only=True,
            save_weights_only=False,
            verbose=verbose)
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=patience)
        reduce_lr = ReduceLROnPlateau(
            monitor='val_loss',
            factor=factor,
            patience=patience,
            verbose=verbose)
        log_dir = "logs/plugins/profile/{}".format(datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
        if os.path.exists(log_dir):
            # 路径已经存在删除路径
            shutil.rmtree(log_dir)
        tensor_board = TensorBoard(
            log_dir=log_dir,
            batch_size=batch_size)

        # 训练模型
        self.model.fit(
            train_x,
            train_y,
            validate_x,
            validate_y,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[checkpoint, early_stopping, reduce_lr, tensor_board]
        )

    def _create_dataset(self, examples):
        X, Y = [], []
        for example in examples:
            entity_offsets = self._convert_example(example)
            data, label = self._predata(example.text, entity_offsets)
            X.append(data)
            Y.append(label)
        return X, Y

    def _convert_example(self, example):
        def convert_entity(entity):
            return entity["start"], entity["end"], entity["entity"]

        return [convert_entity(ent) for ent in example.get("entities", [])]

    def _predata(self, text, entity_offsets):
        value = 'O'
        bilou = [value for _ in text]
        text_list = list(text)

        for (start, end, entity) in entity_offsets:
            if start is not None and end is not None:
                bilou[start] = 'B-' + entity
                for i in range(start + 1, end):
                    bilou[i] = 'I-' + entity

        # # 数据截断
        # if len(bilou) > self.component_config.get('sequence_length'):
        #     bilou = bilou[:self.component_config.get('sequence_length')]
        #     text_list = text_list[:self.component_config.get('sequence_length')]

        # 计算数据集的最大长度
        if len(bilou) > self.sequence_length:
            self.sequence_length = len(bilou)

        return text_list, bilou

    def process(self, message, **kwargs):
        """结果预测"""
        extracted = self.add_extractor_name(self.extract_entities(message))

        message.set("entities",
                    message.get("entities", []) + extracted,
                    add_to_output=True)

    def extract_entities(self, message):
        if self.model is not None:
            text_list = list(message.text)
            # # 数据过长直接截断部分
            # if len(text_list) > self.component_config.get('sequence_length'):
            #     text_list = text_list[:self.component_config.get('sequence_length')]

            entities, result = self.model.predict_entities([text_list], join_chunk=''), []

            for item in entities[0]['labels']:
                result.append({
                    'start': item['start'],
                    'end': item['start'] + len(item['value']),
                    'value': item['value'],
                    'entity': item['entity']
                })

            return result
        else:
            return []

    def persist(self,
                file_name: Text,
                model_dir: Text) -> Optional[Dict[Text, Any]]:
        """模型保存"""
        model_path = os.path.join(model_dir, file_name)

        self.model.save(model_path)

        remove_file = os.path.join(model_path, 'model_weights.h5')
        os.remove(remove_file)
        shutil.move('entity_weights.h5', model_path)
        os.rename(os.path.join(model_path, 'entity_weights.h5'), os.path.join(model_path, 'model_weights.h5'))

        return {"file": file_name}

    @classmethod
    def load(cls,
             meta: Dict[Text, Any],
             model_dir: Optional[Text] = None,
             model_metadata: Optional['Metadata'] = None,
             cached_component: Optional[EntityExtractor] = None,
             **kwargs: Any
             ) -> 'CustomEntityExtractor':
        """模型加载"""
        if model_dir and meta.get("file"):
            file_name = meta.get("file")
            labeling_model = os.path.join(model_dir, file_name)
            loaded_model = kashgari.utils.load_model(labeling_model)

            return cls(component_config=meta,
                       model=loaded_model)
        else:
            logger.warning("Failed to load entity model. Maybe path {} "
                           "doesn't exist"
                           "".format(os.path.abspath(model_dir)))
            return cls(component_config=meta)

