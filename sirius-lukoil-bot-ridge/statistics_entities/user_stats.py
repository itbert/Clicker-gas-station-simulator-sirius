from typing import AnyStr, Any, Callable
from statistics_entities.stats import Stats


def user_value_getter_function(stat_object,
                               scope: 'Scope',
                               user: 'User',
                               stage: 'Stage',
                               metric_name: AnyStr,
                               metric_value: Any):
    if metric_name not in stat_object:
        stat_object[metric_name] = metric_value
    return stat_object[metric_name]


def user_value_setter_function(stat_object,
                               scope: 'Scope',
                               user: 'User',
                               stage: 'Stage',
                               metric_name: AnyStr,
                               metric_value: Any):
    stat_object[metric_name] = metric_value


# Считает статистику для конкретного пользователя, без выделения конкретного этапа.
# К примеру, сколько всего этапов посетил пользоаватель.
class UserStats(Stats):

    def __init__(self,
                 metric_name: AnyStr,
                 metric_value: Any,
                 metric_function: 'Callable[[Scope, User, Stage, Any], ...]'):
        super().__init__(metric_name,
                         metric_value,
                         metric_function,
                         stat_object_getter_function=lambda scope, user, stage: user.try_get_variable("stats", {}),
                         stat_object_setter_function=lambda scope, user, stage, value: user.set_variable("stats", value),
                         value_getter_function=user_value_getter_function,
                         value_setter_function=user_value_setter_function)


# Сколько этапов посетил пользователь.
class UserStatsVisitCount(UserStats):

    def __init__(self,
                 name: AnyStr = "VisitCount"):
        super().__init__(name,
                         lambda scope, user, stage: 0,
                         lambda scope, user, stage, value: value + 1)


# Этап на котором находится пользователь.
class UserStatsCurrentStage(UserStats):

    def __init__(self):
        super().__init__("CurrentStage",
                         lambda scope, user, stage: stage.get_name(),
                         lambda scope, user, stage, value: stage.get_name())
