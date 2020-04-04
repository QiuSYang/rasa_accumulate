rasa 项目说明：适用rasa 1.6.0
    通过语音信息收集与交互，机器自动开门
    
    1. 此项目只是为了熟悉rasa custom policy而写的，没有实际工程价值，仅供学习参考
    2. 自动开门场景：
                    AI：开头语-请问您是谁？
                    USER：我是杨球松(intent: inform, entity: 杨球松)(名字匹配不上，直接请离开)
                    AI: 请您说出开门密码？
                    USER：1234(intent: inform, entity: 1234)（密码不对，请离开）
                    AI：主人，请进！(action_restart, 标志对话结束)
    3. 异常处理：A. user intent 为 bye，thanks，AI：直接回复bye
                B. user intent 为 chat, AI: 直接回复上一次AI的问题，两次以上直接see you
                    
    