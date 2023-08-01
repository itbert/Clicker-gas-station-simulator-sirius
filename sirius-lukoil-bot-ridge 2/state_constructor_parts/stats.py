from __future__ import annotations
from typing import Callable, AnyStr, Optional, TYPE_CHECKING, Any


class Stats:

    def __init__(self,
                 metric_name: AnyStr,
                 metric_value: Any,
                 metric_function: 'Callable[[Scope, User, Stage, Any], ...]',
                 stat_object_getter_function: 'Callable[[Scope, User, Stage], ...]',
                 stat_object_setter_function: 'Callable[[Scope, User, Stage, Any], ...]',
                 value_getter_function: 'Callable[[Any, Scope, User, Stage, AnyStr, Any], ...]',
                 value_setter_function: 'Callable[[Any, Scope, User, Stage, AnyStr, Any], ...]'):
        self._metric_name = metric_name
        self._metric_value = metric_value
        self._metric_function = metric_function
        self._stat_object_getter_function = stat_object_getter_function
        self._stat_object_setter_function = stat_object_setter_function
        self._value_getter_function = value_getter_function
        self._value_setter_function = value_setter_function

    def step(self,
             scope: 'Scope',
             user: 'User',
             stage: 'Stage',
             input_string: Optional[AnyStr] = None):
        stat_object = self._stat_object_getter_function(scope, user, stage)

        metric_value = self._value_getter_function(stat_object, scope, user, stage, self._metric_name,
                                                   self._metric_value)
        metric_value = self._metric_function(scope, user, stage, metric_value)
        self._value_setter_function(stat_object, scope, user, stage, self._metric_name, metric_value)

        self._stat_object_setter_function(scope, user, stage, stat_object)


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


class StageStats(Stats):

    def __init__(self,
                 metric_name: AnyStr,
                 metric_value: Any,
                 metric_function: 'Callable[[Scope, User, Stage, Any], ...]'):
        super().__init__(metric_name,
                         metric_value,
                         metric_function,
                         stat_object_getter_function=lambda scope, user, stage: scope.try_get_variable("stats", {}),
                         stat_object_setter_function=lambda scope, user, stage, value: scope.change_variable("stats", value),
                         value_getter_function=stage_value_getter_function,
                         value_setter_function=stage_value_setter_function)


class StageStatsVisitCount(StageStats):

    def __init__(self):
        super().__init__("VisitCount",
                         0,
                         lambda scope, user, stage, value: value + 1)


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


class UserStats(Stats):

    def __init__(self,
                 metric_name: AnyStr,
                 metric_value: Any,
                 metric_function: 'Callable[[Scope, User, Stage, Any], ...]'):
        super().__init__(metric_name,
                         metric_value,
                         metric_function,
                         stat_object_getter_function=lambda scope, user, stage: user.try_get_variable("stats", {}),
                         stat_object_setter_function=lambda scope, user, stage, value: user.change_variable("stats", value),
                         value_getter_function=user_value_getter_function,
                         value_setter_function=user_value_setter_function)


class UserStatsVisitCount(UserStats):

    def __init__(self):
        super().__init__("VisitCount",
                         0,
                         lambda scope, user, stage, value: value + 1)
