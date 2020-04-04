"""
# 根据场景编写的rule base policy module
"""
import logging
import json
import os
import typing
from typing import Any, List, Text, Optional

import rasa
from rasa.core.domain import Domain, InvalidDomain
from rasa.core.events import ActionExecuted
from rasa.core.policies.policy import Policy
from rasa.core.trackers import DialogueStateTracker
from rasa.core.constants import MAPPING_POLICY_PRIORITY

from rasa.core.actions.action import (
    ACTION_BACK_NAME,
    ACTION_LISTEN_NAME,
    ACTION_RESTART_NAME,
    ACTION_SESSION_START_NAME,
)

_logger = logging.getLogger(__name__)


class SelfRulePolicy(Policy):
    """self rule policy class"""
    def __init__(self, priority: int = MAPPING_POLICY_PRIORITY) -> None:
        """Create a new self rule policy."""

        super().__init__(priority=priority)
        # 记录latest agent ask question
        self.latest_agent_ask_utter = 'utter_ask_own_name'
        # 记录闲聊的次数，超过两次直接表示再见
        self.chat_num = 0
        self.dialogue_id = str()

    @staticmethod
    def _default_predictions(domain: Domain) -> List[float]:
        """Creates a list of zeros.

        Args:
            domain: the :class:`rasa.core.domain.Domain`
        Returns:
            the list of the length of the number of actions
        """

        return [0.0] * domain.num_actions

    def train(
            self,
            training_trackers: List[DialogueStateTracker],
            domain: Domain,
            **kwargs: Any,
    ) -> None:
        """Does nothing. This policy is deterministic."""

        pass

    def predict_action_probabilities(
            self, tracker: DialogueStateTracker, domain: Domain
    ) -> List[float]:
        """Predicts the assigned action."""

        # 更新对话ID
        if tracker.sender_id != self.dialogue_id:
            self.dialogue_id = tracker.sender_id
            self.latest_agent_ask_utter = 'utter_ask_own_name'
            self.chat_num = 0

        prediction = self._default_predictions(domain)

        action = None
        intent = tracker.latest_message.intent.get('name')
        if intent == 'greet':
            if self.chat_num == 0:
                if tracker.latest_action_name == ACTION_LISTEN_NAME:
                    action = 'utter_greet'
                    # 闲聊计数
                    self.chat_num += 1
                elif tracker.latest_action_name == 'utter_greet':
                    # 镜像表达问候之后，追问之前问题
                    action = self.latest_agent_ask_utter
                else:
                    # 追问之后就应该agent就应该去监听用户的回答
                    action = ACTION_LISTEN_NAME
                    # 更新最新的询问, 其实不需要更新，继续保持原样就好
                    self.latest_agent_ask_utter = self.latest_agent_ask_utter
            else:
                # 不予许闲聊两次，greet也算一种chat
                if tracker.latest_action_name == ACTION_LISTEN_NAME:
                    action = 'utter_bye'
                else:
                    action = ACTION_LISTEN_NAME
        elif intent == 'bye':
            # 遇到intent bye 直接弹出
            if tracker.latest_action_name == ACTION_LISTEN_NAME:
                action = 'utter_bye'
            else:
                action = ACTION_LISTEN_NAME
        elif intent == 'thanks':
            # user
            if tracker.latest_action_name == ACTION_LISTEN_NAME:
                action = 'utter_welcome'
            elif tracker.latest_action_name == 'utter_welcome':
                action = 'utter_bye'
            else:
                action = ACTION_LISTEN_NAME
                # 更新最新的询问, 其实不需要更新，继续保持原样就好
                self.latest_agent_ask_utter = self.latest_agent_ask_utter
        elif intent == 'chat':
            if self.chat_num == 0:
                if tracker.latest_action_name == ACTION_LISTEN_NAME:
                    action = 'utter_chat'
                    self.chat_num += 1
                elif tracker.latest_action_name == 'utter_chat':
                    # 追问前一个agent的提问
                    action = self.latest_agent_ask_utter
                else:
                    action = ACTION_LISTEN_NAME
            else:
                if tracker.latest_action_name == ACTION_LISTEN_NAME:
                    action = 'utter_chat'
                elif tracker.latest_action_name == 'utter_chat':
                    action = 'utter_bye'
                else:
                    action = ACTION_LISTEN_NAME
        elif intent == 'inform':
            entities = tracker.latest_message.entities
            if entities:
                if not tracker.get_slot('is_valid_password') is None:
                    # 已经经历了密码匹配
                    if tracker.get_slot('is_valid_password'):
                        # 成功
                        if tracker.latest_action_name == 'utter_validation_pass':
                            action = ACTION_LISTEN_NAME
                        else:
                            # 表达进门，后面再说什么也不在做其他回复，一直回复这句话
                            # 都是为了简化逻辑
                            action = 'utter_validation_pass'
                    elif not tracker.get_slot('is_valid_password'):
                        # 失败
                        if tracker.latest_action_name == 'utter_password_error':
                            action = ACTION_LISTEN_NAME
                        else:
                            # 表达请离开,不管后面在回答任何内容
                            action = 'utter_password_error'
                elif tracker.get_slot('is_own'):
                    # 第二步，匹配密码
                    if tracker.get_slot('password'):
                        # 已经收集到密码，匹配密码
                        action = 'action_match_password'
                    elif tracker.latest_action_name == 'utter_ask_setting_password':
                        # 收集密码的第二步，等待用户的回答
                        action = ACTION_LISTEN_NAME
                    else:
                        # 没有收集到password, 收集密码第一步，提问
                        action = 'utter_ask_setting_password'
                        # 更新最新agent的 ask
                        self.latest_agent_ask_utter = action
                elif tracker.get_slot('name'):
                    # 第一步，匹配姓名
                    if tracker.latest_action_name == ACTION_LISTEN_NAME:
                        action = 'action_match_name'
                    elif tracker.latest_action_name == "utter_own_name_error":
                        # 只要有agent的utter，都将进入agent监状态
                        action = ACTION_LISTEN_NAME
                    elif not tracker.get_slot('is_own'):
                        action = 'utter_own_name_error'
            else:
                if tracker.latest_action_name == ACTION_LISTEN_NAME:
                    # 没有收集到任何实体信息，重新追问上一个问题
                    action = self.latest_agent_ask_utter
                else:
                    action = ACTION_LISTEN_NAME
                    # 更新最新的询问, 其实不需要更新，继续保持原样就好
                    self.latest_agent_ask_utter = self.latest_agent_ask_utter
        else:
            # every dialogue start, no collected any intent(or user utter)
            if tracker.latest_action_name == ACTION_LISTEN_NAME:
                action = self.latest_agent_ask_utter
            else:
                action = ACTION_LISTEN_NAME

        # 获取action的index
        idx = domain.index_for_action(action)
        prediction[idx] = 1

        return prediction

    def persist(self, path: Text) -> None:
        """Only persists the priority."""

        config_file = os.path.join(path, "self_rule_policy.json")
        meta = {"priority": self.priority}
        rasa.utils.io.create_directory_for_file(config_file)
        rasa.utils.io.dump_obj_as_json_to_file(config_file, meta)

    @classmethod
    def load(cls, path: Text) -> "SelfRulePolicy":
        """Returns the class with the configured priority."""

        meta = {}
        if os.path.exists(path):
            meta_path = os.path.join(path, "self_rule_policy.json")
            if os.path.isfile(meta_path):
                meta = json.loads(rasa.utils.io.read_file(meta_path))

        return cls(**meta)
