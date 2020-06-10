"""
# 自定义agent
"""
import os
import sys
import warnings
import logging
from rasa.core.agent import Agent
from typing import Text, List, Optional, Callable, Any, Dict, Union
from rasa.core.channels import UserMessage, OutputChannel

logger = logging.getLogger(__name__)


class HciAgent(Agent):
    # 继承，如果构造函数需要新添加内容，
    # 才继承构造函数，并且需要添加父类的全部参数
    # def __init__(self):
    #     super().__init__()

    async def handle_text(self,
                          nlu_info: Optional[Dict],
                          message_preprocessor: Optional[Callable[[Text], Text]] = None,
                          output_channel: Optional[OutputChannel] = None,
                          sender_id: Optional[Text] = UserMessage.DEFAULT_SENDER_ID
                          ) -> Optional[List[Dict[Text, Any]]]:
        """Handle a single message.

        If a message preprocessor is passed, the message will be passed to that
        function first and the return value is then used as the
        input for the dialogue engine.

        The return value of this function depends on the ``output_channel``. If
        the output channel is not set, set to ``None``, or set
        to ``CollectingOutputChannel`` this function will return the messages
        the bot wants to respond.

        这个地方的输入是经过NLU提取之后的意图和实体Json(dict)."""

        # 进行输入数据的整合
        if isinstance(nlu_info, dict):
            msg = UserMessage(output_channel=output_channel,
                              sender_id=sender_id, parse_data=nlu_info)
        else:
            # 如果nlu_info不是dict类型直接抛出异常
            raise TypeError("The nlu input data type must be a dictionary.")

        return await self.handle_message(msg, message_preprocessor)
