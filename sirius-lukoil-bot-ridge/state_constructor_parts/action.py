from __future__ import annotations
from typing import Callable, AnyStr, Optional, TYPE_CHECKING, Any


# Определяет действие, активация которого происходит во время обработки пользовательского ответа
# на определённом этапе. Из-за этого у такого действия есть строке ввода пользователя.
from telegram import Message, Bot


class Action:

    def __init__(self,
                 action_function: 'Callable[[Scope, User, Optional[AnyStr], Optional[Bot]], ...]'):
        self._action_function = action_function

    def apply(self,
              scope: 'Scope',
              user: 'User',
              input_string: Optional[AnyStr] = None,
              telegram_bot: Optional[Bot] = None):
        self._action_function(scope, user, input_string, telegram_bot)


# Определяет действие, активация которого происходит в момент посылки пользователю сообщения.
# Из-за этого у такого действия есть доступ к посланному Message в момент применения.
class PrerequisiteAction:

    def __init__(self,
                 action_function: 'Callable[[Scope, User, Optional[Message], Bot], ...]'):
        self._action_function = action_function

    def apply(self,
              scope: 'Scope',
              user: 'User',
              sent_message: Optional[Message] = None,
              telegram_bot: Optional[Bot] = None):
        self._action_function(scope, user, sent_message, telegram_bot)


class ActionBack(Action):
    def __init__(self):
        super().__init__(lambda scope, user, input_string, bot: user.change_stage(user.get_stage_history()[-2]))


class ActionBackToMainStage(Action):
    def __init__(self):
        super().__init__(lambda scope, user, input_string, bot: user.change_stage(scope.get_main_stage_name()))


class ActionChangeStage(Action):
    def __init__(self,
                 stage_name: AnyStr):
        super().__init__(lambda scope, user, input_string, bot: user.change_stage(stage_name))


class ActionChangeUserVariable(Action):
    def __init__(self,
                 variable_name: AnyStr,
                 variable_value: Any):
        if callable(variable_value):
            super().__init__(lambda scope, user, input_string, bot: user.set_variable(variable_name, variable_value(scope, user)))
        else:
            super().__init__(lambda scope, user, input_string, bot: user.set_variable(variable_name, variable_value))


class ActionChangeUserVariableToInput(Action):
    def __init__(self,
                 variable_name: AnyStr):
        super().__init__(lambda scope, user, input_string, bot: user.set_variable(variable_name, input_string))


class ActionChangeGlobalVariable(Action):
    def __init__(self,
                 variable_name: AnyStr,
                 variable_value: AnyStr):
        super().__init__(lambda scope, user, input_string, bot: scope.set_variable(variable_name, variable_value))


class ActionGetInput(Action):
    def __init__(self):
        super().__init__(lambda scope, user, input_string, bot: input_string)
