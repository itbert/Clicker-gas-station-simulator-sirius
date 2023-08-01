from __future__ import annotations

from datetime import datetime
from typing import List, AnyStr, Dict, Any, Optional, Callable
from data_access_layer.database import Database
from statistics_entities.stats import Stats


class User:
    _stage_history: List[AnyStr]
    _user_variables: Dict[AnyStr, AnyStr]
    _common_statistics: Optional[List[Stats]]  # Статистика, подсчет которой ведется для всех пользователей.

    @staticmethod
    def set_common_statistics(statistics: List[Stats]):
        User._common_statistics = statistics

    def __init__(self,
                 chat_id: AnyStr,
                 nickname: AnyStr):
        self.chat_id = chat_id

        if not Database.is_user_exist(chat_id):
            Database.add_user(chat_id, ['NewUser'], {"_nickname": nickname, "added_date": int(datetime.today().timestamp())})

        self.update_info()

    def update_info(self):
        user_from_db = Database.get_user(self.chat_id)

        self._stage_history = user_from_db['stage_history']
        self._user_variables = user_from_db['user_variables']

    def get_current_stage_name(self) -> AnyStr:
        return self._stage_history[-1]

    def change_stage(self,
                     stage_name: AnyStr):
        self._stage_history.append(stage_name)
        Database.change_user_column(self.chat_id, 'stage_history', self._stage_history)

    def set_variable(self,
                     variable_name: AnyStr,
                     variable_value: Any | Callable[[Any], Any]):
        self._user_variables[variable_name] = variable_value
        Database.change_user_column(self.chat_id, 'user_variables', self._user_variables)

    def change_variable(self,
                        variable_name: AnyStr,
                        change_method: Callable[[Any], Any],
                        default_value: Any):
        self._user_variables[variable_name] = change_method(self.try_get_variable(variable_name, default_value))
        Database.change_user_column(self.chat_id, 'user_variables', self._user_variables)

    def try_get_variable(self,
                         variable_name: AnyStr,
                         default_value: Any):
        value = self.get_variable(variable_name)
        if value is None:
            self.set_variable(variable_name, default_value)
            return default_value
        return value

    def get_variable(self,
                     variable_name: str):
        try:
            self.update_info()
            return self._user_variables[variable_name]
        except Exception:
            return None

    def get_stage_history(self):
        return self._stage_history

    def delete(self):
        Database.delete_user(self.chat_id)

    def _get_statistics(self, scope, user):
        return User._common_statistics or []

    def count_statistics(self,
                         input_string: AnyStr,
                         scope: 'Scope',
                         user: 'User',
                         stage: 'Stage'):
        if statistics := self._get_statistics(scope, user):
            for statistic in statistics:
                statistic.step(scope, user, stage, input_string)
