import logging
from typing import Dict, Optional, AnyStr, List, Any

from data_access_layer.database import Database


class Scope:

    _global_variables: Dict[AnyStr, AnyStr]

    def __init__(self,
                 stages: 'List[Stage]',
                 main_stage_name: AnyStr):
        self._stages = stages
        self._main_stage_name = main_stage_name
        self._global_variables = {}

        self.update_info()

    def get_main_stage_name(self) -> AnyStr:
        return self._main_stage_name

    def update_info(self):
        scope_from_db = Database.get_scope()
        self._global_variables = scope_from_db['global_variables']

    def set_variable(self,
                     variable_name: AnyStr,
                     variable_value: AnyStr):
        self._global_variables[variable_name] = variable_value
        Database.change_scope_column('global_variables', self._global_variables)

    def get_variable(self,
                     variable_name: AnyStr):
        self.update_info()
        try:
            return self._global_variables[variable_name]
        except Exception:
            return None

    def try_get_variable(self,
                         variable_name: AnyStr,
                         default_value: Any):
        value = self.get_variable(variable_name)
        if value is None:
            self.set_variable(variable_name, default_value)
            return default_value
        return value

    def get_stage(self,
                  stage_name: AnyStr) -> 'Optional[Stage]':
        for stage in self._stages:
            if stage.get_name() == stage_name:
                return stage

    def add_stage(self,
                  stage: 'Stage'):
        logging.info("Stages now is {}".format(self._stages))
        self._stages.append(stage)

    def add_stages(self,
                   stages: 'List[Stage]'):
        self._stages.extend(stages)
