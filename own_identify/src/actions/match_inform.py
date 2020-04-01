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
    own_name = '杨球松'

    def name(self):  # type: () -> Text
        return 'action_match_name'



class ActionMatchPassword(Action):
    """匹配 own 设置密码是否匹配"""
    own_password = '20200202'

    def name(self):  # type: () -> Text
        return 'action_match_password'
