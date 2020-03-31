"""
# 匹配信息的有效性
"""
import os
import logging
from rasa_sdk import Action
from rasa_sdk.events import SlotSet

_logger = logging.getLogger(__name__)


class ActionMatchName(Action):
    own_name = '杨球松'


class ActionMatchPassword(Action):
    own_password = '20200202'
