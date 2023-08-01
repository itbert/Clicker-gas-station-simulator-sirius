import hashlib
import logging
from global_transferable_entities.user import User
from state_constructor_parts.action import ActionChangeUserVariableToInput, ActionChangeStage, Action, ActionBack,\
    ActionChangeUserVariable, ActionBackToMainStage
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

# 1 3 1

    def counterAnswer(scope, user, input_string, bot):
        countRightAnswer = user.get_variable("counter")
        countRightAnswer += 1
        user.set_variable("counter", countRightAnswer)

    def perehod(scope, user):
        QA = user.get_variable("counter")
        if QA == 3:
            pass
        else:
            return MessageKeyboard(
                buttons=[
                    MessageKeyboardButton(
                        text="Попробовать снова 🍁",
                        actions=[ActionChangeStage("opros")])])


    def otvet1st(scope, user):
        QA = user.get_variable("counter")
        if QA == 3:
            password = hashlib.sha256((str(user.chat_id) + "3").encode()).hexdigest()[:4]
            return f"‣ Вы ответили на все вопросы правильно, позравляем!🍤.🎉 \nПароль для перехода на следующую должность → {password}"
        else:
            return "× Вы ответили не на все вопросы правильно ಥ_ಥ. \nПопробуйте пройти тест еще раз ↩"


    _scope = Scope([

        Stage(name="NewUser",
              user_input_actions=[ActionChangeUserVariable("counter", 0),
                                  ActionChangeStage("opros")]),

        Stage(name="opros",
              message=Message(text="Уважаемый директор, у нас произошла утечка нефти из баков. Что нам следует делать?"
                                   "\n\n1⁝ Срочно прекращать слив нефтепродуктов! 🔧"
                                   "\n2⁝ Думаю, мы можем закрыть на это глаза. Опасность не такая большая 😅"
                                   "\n3⁝ Очевидно, нам следует манкировать планом ⚙📜 действий по предупреждению и "
                                   "ликвидации разливов нефти и нефтепродуктов",

                              keyboard=MessageKeyboard(
                                  buttons=[
                                      MessageKeyboardButton(text="1",
                                                            actions=[Action(counterAnswer),
                                                                     ActionChangeStage("1")]),
                                      MessageKeyboardButton(text="2",
                                                            actions=[ActionChangeStage("1")]),
                                      MessageKeyboardButton(text="3",
                                                            actions=[ActionChangeStage("1")])
                                  ]
                              )),
              prerequisite_actions=[ActionChangeUserVariable("counter", 0)]),

        Stage(name="1",
              message=Message(text="Босс, аналитики сообщили, что скоро ожидается падение цен на нефть...🥶 "
                                   "Какое ваше распоряжение?"
                                   "\n\n1⁝ Нужно увеличивать долю доходов от отраслей, "
                                   "связанных с добычей и реализацией нефти. "
                                   "\n2⁝ Мы ни в коем случае не должны инвестировать "
                                   "в просевшие акции добывающих компаний. 🙄"
                                   "\n3⁝ Мы должны закупить валюту в ближайшее время.🤑",

                              keyboard=MessageKeyboard(
                                  buttons=[
                                      MessageKeyboardButton(text="1",
                                                            actions=[ActionChangeStage("2")]),
                                      MessageKeyboardButton(text="2",
                                                            actions=[ActionChangeStage("2")]),
                                      MessageKeyboardButton(text="3",
                                                            actions=[Action(counterAnswer),
                                                                     ActionChangeStage("2")]),
                                  ]
                              ))),

        Stage(name="2",
              message=Message(text="Начальник, нам нужно продать 3 барреля из последней поставки. Сколько это в литрах?"
                                   "\n\n1⁝ Продаем 477 литров 🛒"
                                   "\n2⁝ Загружайте 520 литров 📣"
                                   "\n3⁝ 496 литров. Работаем 🚇",
                              keyboard=MessageKeyboard(
                                  buttons=[
                                      MessageKeyboardButton(text="1",
                                                            actions=[Action(counterAnswer),
                                                                     ActionChangeStage("otvet1stage")]),
                                      MessageKeyboardButton(text="2",
                                                            actions=[ActionChangeStage("otvet1stage")]),
                                      MessageKeyboardButton(text="3",
                                                            actions=[ActionChangeStage("otvet1stage")])

                                  ]
                              ))),

        Stage(name="otvet1stage",
              message=Message(text=otvet1st,
                              keyboard=perehod))
    ], main_stage_name="Main")

    logging.info("Program started")

    bot = Bot('<PasteYourTokenHere>', _scope)

    bot.start_polling(poll_interval=2,
                      poll_timeout=1)
