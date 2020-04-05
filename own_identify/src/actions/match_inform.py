"""
# 匹配信息的有效性
"""
import os
import logging
from rasa_sdk import Action
from rasa_sdk.events import SlotSet

_logger = logging.getLogger(__name__)


class ActionMatchName(Action):
    """匹配 own 姓名是否正确"""
    own_name = '孙悟空'

    def name(self):  # type: () -> Text
        return 'action_match_name'

    def run(
            self,
            dispatcher,  # type: CollectingDispatcher
            tracker,  # type: Tracker
            domain,  # type:  Dict[Text, Any]
    ):  # type: (...) -> List[Dict[Text, Any]]
        slots = []

        if tracker.get_slot('name'):
            if tracker.get_slot('name') == self.own_name:
                # 再询问密码
                slots.append(SlotSet('is_own', True))
            else:
                # 名字不对，直接拜拜(不支持修正)
                slots.append(SlotSet('is_own', False))

        return slots


class ActionMatchPassword(Action):
    """匹配 own 设置密码是否匹配"""
    own_password = '20200202'

    def name(self):  # type: () -> Text
        return 'action_match_password'

    def run(
            self,
            dispatcher,  # type: CollectingDispatcher
            tracker,  # type: Tracker
            domain,  # type:  Dict[Text, Any]
    ):  # type: (...) -> List[Dict[Text, Any]]
        slots = []

        if tracker.get_slot('password'):
            if tracker.get_slot('password') == self.own_password:
                slots.append(SlotSet('is_valid_password', True))
                # 执行开门指令
                _logger.info("open the door.")
            else:
                # 密码不对，直接拜拜(不支持修正)
                slots.append(SlotSet('is_valid_password', False))

        return slots
