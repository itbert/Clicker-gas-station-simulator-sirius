import hashlib
import logging
from global_transferable_entities.user import User
from state_constructor_parts.action import ActionChangeUserVariableToInput, ActionChangeStage, Action, ActionBack, ActionChangeUserVariable
from bot import Bot
from message_parts.message import Message, MessageKeyboard, MessageKeyboardButton, MessagePicture
from global_transferable_entities.scope import Scope
from state_constructor_parts.stage import Stage
from statistics_entities.stage_stats import StageStatsVisitCount
from statistics_entities.user_stats import UserStatsVisitCount, UserStatsCurrentStage

if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO,
                        filename='log.txt')
    logging.info("Program started")

    Stage.set_common_statistics([StageStatsVisitCount()])
    User.set_common_statistics([UserStatsVisitCount(),
                                UserStatsCurrentStage()])

    # --- Helper methods ---

    def count_right_answer(scope, user, input_string, bot):
        right_answers_count = user.try_get_variable("right_answers_count", 0)
        right_answers_count += 1
        user.set_variable("right_answers_count", right_answers_count)

    def generate_final_text(scope, user):
        right_answers_count = user.try_get_variable("right_answers_count", 0)
        if right_answers_count == 3:
            password = hashlib.sha256((str(user.chat_id) + "2").encode()).hexdigest()[:4]
            return f"✔ Вы успешно прошли тест, ваш пароль: {password}"
        else:
            return "❌ Вы ответели не на все вопросы правильно.\nПопробуйте пройти тест еще раз"

    def zero_answers(scope, user, input_string, bot):
        user.set_variable("right_answers_count", 0)

    def generate_final_keyboard(scope, user):
        right_answers_count = user.try_get_variable("right_answers_count", 0)
        if right_answers_count == 3:
            return None
        else:
            return MessageKeyboard(
                [
                    MessageKeyboardButton(
                        text="Пройти тест еще раз",
                        actions=[ActionChangeStage("Main"), Action(zero_answers)]
                    )
                ]
            )

    # --- State constructor ---

    _scope = Scope([

        Stage(name="NewUser",
              user_input_actions=[ActionChangeStage("Main"), Action(zero_answers)]),

        Stage(name="Main",
              message=Message(
                  text="😎 Босс! Обанкротившаяся компания предлагает нам нефть. Цены одинаковы на все виды. Какую берем?\n\n1) Берем твердую\n2) Берем традиционную\n3) Берем легкую",
                  keyboard=MessageKeyboard(
                      buttons=[
                          MessageKeyboardButton(text="1",
                                                actions=[ActionChangeStage("Stage2")]),
                          MessageKeyboardButton(text="2",
                                                actions=[ActionChangeStage("Stage2")]),
                          MessageKeyboardButton(text="3",
                                                actions=[ActionChangeStage("Stage2"), Action(count_right_answer)])
                      ]
                  )
              )),


        Stage(name="Stage2",
              message=Message(
                  text="🙂 Начальник, мы открываем новый завод, на который приедет комиссия, где его расположить?\n\n1) Место нефтедобычи \n2) Место потребления нефтепродуктов \n3) Место скопления нефтепродуктов",
                  keyboard=MessageKeyboard(
                      buttons=[
                          MessageKeyboardButton(text="1",
                                                actions=[ActionChangeStage("Stage3")]),
                          MessageKeyboardButton(text="2",
                                                actions=[ActionChangeStage("Stage3"), Action(count_right_answer)]),
                          MessageKeyboardButton(text="3",
                                                actions=[ActionChangeStage("Stage3")]),
                      ]
                  )
              )),

        Stage(name="Stage3",
              message=Message(
                  text="💸 😎 Босс, новая поставка нашим сотрудникам из Китая готова к отправке, осталось лишь выбрать на чем ее повезут.\n\n1) Везите на танкере \n2) Перевезите нефтепроводом \n3) Везите по трассе",
                  keyboard=MessageKeyboard(
                      buttons=[
                          MessageKeyboardButton(text="1",
                                                actions=[ActionChangeStage("Stage4")]),
                          MessageKeyboardButton(text="2",
                                                actions=[ActionChangeStage("Stage4"), Action(count_right_answer)]),
                          MessageKeyboardButton(text="3",
                                                actions=[ActionChangeStage("Stage4")]),
                      ]
                  )
              )),

        Stage(name="Stage4",
              message=Message(
                  text=generate_final_text,
                  keyboard=generate_final_keyboard))



    ], main_stage_name="Main")

    logging.info("Program started")

    bot = Bot('<PASTE_YOUR_TOKEN_HERE>', _scope)

    bot.start_polling(poll_interval=2,
                      poll_timeout=1)
