from __future__ import annotations

import itertools
from typing import List, AnyStr, Optional, Callable

from telegram import Bot

from global_transferable_entities.scope import Scope
from global_transferable_entities.user import User
from state_constructor_parts.action import Action, PrerequisiteAction
from state_constructor_parts.filter import InputFilter
from message_parts.message import Message
from statistics_entities.stats import Stats
from typing_module_extensions.instance_or_callable import InstanceOrCallable


class Stage:
    _common_statistics: Optional[List[Stats]]  # Статистика, подсчет которой ведется для всех этапов.

    @staticmethod
    def set_common_statistics(statistics: List[Stats]):
        Stage._common_statistics = statistics

    def __init__(self,
                 name: AnyStr,
                 message: Optional[Message | Callable[..., Message]] = None,
                 prerequisite_actions: Optional[List[PrerequisiteAction] | Callable[..., List[PrerequisiteAction]]] = None,
                 user_input_actions: Optional[List[Action] | Callable[..., List[Action]] | List[Callable[..., Action]] | Callable[..., List[Callable[..., Action]]]] = None,
                 user_input_filter: Optional[InputFilter | Callable[..., InputFilter]] = None,
                 statistics: Optional[List[Stats]] = None,
                 is_gatehouse: bool = False,  # TODO: Автоматическое определение IsGatehouse в зависимости от прикрепленных actions.
                 sending_message_error_actions: Optional[List[PrerequisiteAction] | Callable[..., List[PrerequisiteAction]]] = None):
        self._name = name
        self._message = InstanceOrCallable(message)
        self._prerequisite_actions = InstanceOrCallable(prerequisite_actions)
        self._user_input_actions = InstanceOrCallable(user_input_actions)
        self._sending_message_error_actions = InstanceOrCallable(sending_message_error_actions)
        self._user_input_filter = InstanceOrCallable(user_input_filter)
        self._statistics = statistics
        self._is_gatehouse = is_gatehouse

        # logging.info("Stage with name {} created".format(self._name))

    def is_gatehouse(self) -> bool:
        return self._is_gatehouse

    def get_name(self) -> AnyStr:
        return self._name

    def get_message(self,
                    scope: Scope,
                    user: User) -> Optional[Message]:
        return self._message.get(scope, user)

    def get_prerequisite_actions(self,
                                 scope: Scope,
                                 user: User) -> List[Action]:
        return self._prerequisite_actions.get(scope, user) or []

    def get_user_input_actions(self,
                               scope: Scope,
                               user: User) -> List[Action]:
        return self._user_input_actions.get(scope, user) or []

    def get_sending_message_error_actions(self,
                                          scope: Scope,
                                          user: User) -> List[Action]:
        return self._sending_message_error_actions.get(scope, user) or []

    def _get_statistics(self,
                       scope: Scope,
                       user: User) -> Optional[List[Stats]]:
        return (Stage._common_statistics or []) + (self._statistics or [])

    def get_user_input_filter(self,
                              scope: Scope,
                              user: User) -> Optional[InputFilter]:
        return self._user_input_filter.get(scope, user)

    def is_allowed_input(self,
                         input_string: AnyStr,
                         scope: Scope,
                         user: User) -> bool:
        if input_filter := self.get_user_input_filter(scope, user) is not None:
            if not input_filter.is_allowed_input(input_string):
                return False

        if message := self.get_message(scope, user):
            if keyboard := message.get_keyboard(scope, user):
                if not keyboard.is_non_keyboard_input_allowed:
                    keyboard_buttons_strings = \
                        [button.get_text(scope, user) for button in
                         list(itertools.chain(*keyboard.get_buttons(scope, user)))]
                    if input_string not in keyboard_buttons_strings:
                        return False
        return True

    def count_statistics(self,
                         input_string: AnyStr,
                         scope: Scope,
                         user: User,
                         stage: Stage):
        if statistics := self._get_statistics(scope, user):
            for statistic in statistics:
                statistic.step(scope, user, stage, input_string)

    def process_sending_message_error_actions(self,
                                              scope: Scope,
                                              user: User,
                                              telegram_bot: Bot):
        if sending_message_error_actions := self.get_sending_message_error_actions(scope, user):
            for sending_message_error_action in sending_message_error_actions:
                sending_message_error_action.apply(scope, user, telegram_bot= telegram_bot)

    def process_input(self,
                      input_string: AnyStr,
                      scope: Scope,
                      user: User,
                      telegram_bot: Bot) -> Message:

        if not self.is_allowed_input(input_string, scope, user):
            transition_user_stage = scope.get_stage(user.get_current_stage_name())
            transition_user_message = transition_user_stage.get_message(scope, user)
            transition_user_message.set_onetime_text_processor_method(lambda text: "Выберите один из вариантов и нажмите.\n\n" + text)
            return transition_user_message

        if user_input_actions := self.get_user_input_actions(scope, user):
            for user_input_action in user_input_actions:
                InstanceOrCallable(user_input_action)\
                    .get(scope, user)\
                    .apply(scope, user, input_string, telegram_bot)

        try:
            keyboard_buttons = list(itertools.chain(*self.get_message(scope, user).get_keyboard(scope, user).get_buttons(scope, user)))
            for keyboard_button in keyboard_buttons:
                if input_string == keyboard_button.get_text(scope, user):
                    for action in keyboard_button.get_actions(scope, user):
                        if action is not None:
                            InstanceOrCallable(action)\
                                .get(scope, user)\
                                .apply(scope, user, input_string, telegram_bot)
        except AttributeError:
            pass

        transition_user_stage = scope.get_stage(user.get_current_stage_name())
        return transition_user_stage.get_message(scope, user)
