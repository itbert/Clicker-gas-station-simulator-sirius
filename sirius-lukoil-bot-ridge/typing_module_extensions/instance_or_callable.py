import inspect
import logging
from typing import Callable, TypeVar, Dict, Any, Generic, TYPE_CHECKING, Type

T = TypeVar('T')


class InstanceOrCallable(Generic[T]):
    def __init__(self,
                 instance: 'Callable[[Scope, User], T] | T'):
        self._instance = instance

    def get(self,
            scope: 'Scope',
            user: 'User') -> T:
        # Из-за того, что Callable в данном случае может возвращать другой Callable, надо проверить, что Callable действительно
        # используется в контексте получения обьекта по scope, user.
        # Для этого проверяем, что Callable в виде своих параметров принимает scope, user.
        # Кроме того, нужно проверить что все lambda, использующие только один из параметров [scope, user] а другой из них shadow "_",
        # тоже определяются этой проверкой, поэтому находим совпадения во всех возможных постановках параметров (Включая оба неиспользуемых _, __)
        # Возможны коллизии если в возвращаемом lambda используются два неименованных параметров _ и __.
        # TODO: Разобраться, могут ли быть воозще функции, работающие со scope, user и не использующие ни один из этих параметров.
        # TODO: Логика с такой проверкой не самая элегантная, придумать другую или убрать все возможные instance, возвращающие
        # TODO: callable. Проверить можно по typeChecking 'Callable[..., Callable[', если их убрать оставить только проверку на callable.
        if callable(self._instance) and list(inspect.signature(self._instance).parameters.keys()) in [["scope", "user"], ["_", "user"], ["scope", "_"], ["_", "__"]]:
            return self._instance(scope, user)
        else:
            return self._instance
