from __future__ import annotations

import logging
from typing import Callable, AnyStr, Optional, Any


class Stats:

    def __init__(self,
                 metric_name: AnyStr,
                 metric_value: 'Callable[[Scope, User, Stage], ...]',
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
        logging.info("Изменение значения статистики для метрики {}".format(self._metric_name))
        stat_object = self._stat_object_getter_function(scope,
                                                        user,
                                                        stage)
        metric_value = self._value_getter_function(stat_object,
                                                   scope,
                                                   user,
                                                   stage,
                                                   self._metric_name,
                                                   self._metric_value(scope, user, stage))
        logging.info("Прошлое значение метрики {}".format(metric_value))
        metric_value = self._metric_function(scope,
                                             user,
                                             stage,
                                             metric_value)
        logging.info("Текущее значение метрики {}".format(metric_value))
        self._value_setter_function(stat_object,
                                    scope,
                                    user,
                                    stage,
                                    self._metric_name,
                                    metric_value)
        self._stat_object_setter_function(scope,
                                          user,
                                          stage,
                                          stat_object)

