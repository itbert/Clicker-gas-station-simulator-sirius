from typing import AnyStr, Any, Callable
from statistics_entities.stats import Stats


def stage_value_getter_function(stat_object,
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


def stage_value_setter_function(stat_object,
                                scope: 'Scope',
                                user: 'User',
                                stage: 'Stage',
                                metric_name: AnyStr,
                                metric_value: Any):
    if stage.get_name() not in stat_object:
        stat_object[stage.get_name()] = {}
    if metric_name not in stat_object[stage.get_name()]:
        stat_object[stage.get_name()][metric_name] = metric_value
    stat_object[stage.get_name()][metric_name] = metric_value


# Считает статистику для конкретого этапа, не выделяя при этом пользователей.
# К примеру, сколько конкретный этап посетило пользователей.
class StageStats(Stats):

    def __init__(self,
                 metric_name: AnyStr,
                 metric_value: Any,
                 metric_function: 'Callable[[Scope, User, Stage, Any], ...]'):
        super().__init__(metric_name,
                         metric_value,
                         metric_function,
                         stat_object_getter_function=lambda scope, user, stage: scope.try_get_variable("stats", {}),
                         stat_object_setter_function=lambda scope, user, stage, value: scope.set_variable("stats", value),
                         value_getter_function=stage_value_getter_function,
                         value_setter_function=stage_value_setter_function)


class StageStatsVisitCount(StageStats):  # Сколько человек посетили этап.

    def __init__(self):
        super().__init__("VisitCount",
                         lambda scope, user, stage: 0,
                         lambda scope, user, stage, value: value + 1)
