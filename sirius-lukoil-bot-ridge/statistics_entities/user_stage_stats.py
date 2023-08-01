from typing import AnyStr, Any, Callable
from stats import Stats


def user_stage_value_getter_function(stat_object,
                                     scope: 'Scope',
                                     user: 'User',
                                     stage: 'Stage',
                                     metric_name: AnyStr,
                                     metric_value: Any):
    if stage.get_name() not in stat_object:
        stat_object[stage.get_name()] = {}
    if metric_name not in stat_object[stage.get_name()]:
        stat_object[stage.get_name()][metric_name] = metric_value
    return stat_object[stage.get_name()][metric_name]


def user_stage_value_setter_function(stat_object,
                                     scope: 'Scope',
                                     user: 'User',
                                     stage: 'Stage',
                                     metric_name: AnyStr,
                                     metric_value: Any):
    if stage.get_name() not in stat_object:
        stat_object[stage.get_name()] = {}
    stat_object[stage.get_name()][metric_name] = metric_value


# Считает статистику пользователя и этапа в связке.
# К примеру, сколько пользователь посетил конкретный этап.
# Такая статистика считается для каждого пользователя отдельно.
class UserStageStats(Stats):

    def __init__(self,
                 metric_name: AnyStr,
                 metric_value: Any,
                 metric_function: 'Callable[[Scope, User, Stage, Any], ...]'):
        super().__init__(metric_name,
                         metric_value,
                         metric_function,
                         stat_object_getter_function=lambda scope, user, stage: user.try_get_variable("stats", {}),
                         stat_object_setter_function=lambda scope, user, stage, value: user.set_variable("stats", value),
                         value_getter_function=user_stage_value_getter_function,
                         value_setter_function=user_stage_value_setter_function)


class UserStageStatsVisitTime(UserStageStats):  # Сколько этапов посетил пользователь.

    def __init__(self,
                 name: AnyStr = "VisitCount"):
        super().__init__(name,
                         lambda scope, user, stage: 0,
                         lambda scope, user, stage, value: value + 1)

