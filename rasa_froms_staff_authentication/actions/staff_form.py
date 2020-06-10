"""
# staff 正确回答agent问题进门
"""
from typing import Dict, Text, Any, List, Union, Optional

from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormAction

from pypinyin import lazy_pinyin
from tool.load_database import LoadDB


class StaffForm(FormAction):
    """Example of a staff custom form action"""
    staff_csv_path = "data/database/staff.csv"
    staff_db_info_dicts = LoadDB.load_db_info(staff_csv_path)
    same_staff_name = None

    def name(self) -> Text:

        return "staff_form"

    @staticmethod
    def required_slots(tracker: "Tracker") -> List[Text]:
        """A list of required slots that the form has to fill"""

        # return ["is_staff",
        #         "self_name", "is_valid_staff",
        #         "digits_key", "is_valid_digits_key"]
        return ["self_name", "digits_key"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict[Text, Any]]]]:
        """A dictionary to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""

        return {
            "self_name": self.from_entity(entity="e_name"),
            "digits_key": self.from_entity(entity="e_four_digits"),
            }

    def submit(
        self,
        dispatcher: "CollectingDispatcher",
        tracker: "Tracker",
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Define what the form has to do
                    after all required slots are filled"""

        # utter submit template
        dispatcher.utter_message(template="utter_submit")

        return []

    # USED FOR DOCS: do not rename without updating in docs
    def validate_self_name(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate self_name value."""
        if self.match_staff_name(value) is True:
            return {"self_name": value}
        else:
            if tracker.get_slot("staff_name_error_count") < 1:
                dispatcher.utter_message(template="utter_wrong_self_name")
                # validation failed, set this slot to None, meaning the
                # user will be asked for the slot again

                return {"self_name": None,
                        "staff_name_error_count": tracker.get_slot("staff_name_error_count") + 1}
            else:
                # 呼叫前台
                dispatcher.utter_message(template="utter_manual_service")

                # 中断form
                print("中断 form loop")
                return self.deactivate()

    def validate_digits_key(
            self,
            value: Text,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate digits_key value."""
        if self.match_staff_digits_key(value) is True:
            return {"digits_key": value}
        else:
            if tracker.get_slot("digits_key_error_count") < 1:
                dispatcher.utter_message(template="utter_wrong_digits_key")
                # validation failed, set this slot to None, meaning the
                # user will be asked for the slot again

                return {"digits_key": None,
                        "digits_key_error_count": tracker.get_slot("digits_key_error_count") + 1}
            else:
                # 呼叫前台
                dispatcher.utter_message(template="utter_manual_service")

                # 中断form
                print("中断 form loop")
                return self.deactivate()

    def match_staff_name(self, staff_name):
        """匹配员工姓名"""
        # 人名转换为拼音 python 2 还需要解码编码
        try:
            staff_name_pinyin = ''.join(lazy_pinyin(staff_name))
        except AssertionError:
            print("staff name: {}".format(staff_name))
            return False

        # staff_name_pinyin = ''.join(lazy_pinyin(staff_name.decode('utf-8')).encode('utf-8'))
        # 获取此姓名员工的基本信息
        self.same_staff_name = LoadDB.get_staff_same_name(self.staff_db_info_dicts,
                                                          input_name=staff_name_pinyin)
        if self.same_staff_name and len(self.same_staff_name.get('index')) > 0:
            # 员工名字有效
            return True
        else:
            # 员工名字无效
            return False

    def match_staff_digits_key(self, digits_key):
        """匹配员工的数字密码"""
        # 判断是否有员工姓名被收集到
        if self.same_staff_name:
            # 设置数字密码统计flag
            digits_key_flag = False
            staff_reality_name = None
            for nameId in self.same_staff_name.get('index'):
                if (not self.staff_db_info_dicts.get('info').get(nameId).get('数字密码')
                        and digits_key == self.staff_db_info_dicts.get('info').get(nameId).get('工号')[-4:]):
                    # 没有设置数字密码，默认为工号后四位
                    digits_key_flag = True
                    staff_reality_name = self.staff_db_info_dicts.get('info').get(nameId).get('员工姓名')
                    break
                elif (self.staff_db_info_dicts.get('info').get(nameId).get('数字密码')
                      and digits_key == self.staff_db_info_dicts.get('info').get(nameId).get('数字密码')[-4:]):
                    # 员工有设置数字密码
                    digits_key_flag = True
                    staff_reality_name = self.staff_db_info_dicts.get('info').get(nameId).get('员工姓名')
                    break
            if digits_key_flag:
                # # 数据清零
                # self.same_staff_name = None

                # 员工数字密码有效
                return True
            else:
                # # 数据清零
                # self.same_staff_name = None

                # 员工数字密码无效
                return False
        else:
            # # 数据清零
            # self.same_staff_name = None

            return False
