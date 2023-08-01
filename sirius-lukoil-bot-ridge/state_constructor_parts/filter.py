import logging
import re
from typing import AnyStr, Pattern, Callable


class InputFilter:
    def __init__(self,
                 filter_regex: Pattern[AnyStr] = None,
                 filter_function: Callable = None,
                 not_passed_reason_message: AnyStr = None):
        self.filter_regex = filter_regex
        self.filter_function = filter_function
        self.not_passed_reason_message = not_passed_reason_message

    def is_allowed_input(self,
                         input_text: AnyStr) -> bool:
        if self.filter_regex is not None:
            return self.filter_regex.match(input_text) is not None
        elif self.filter_function is not None:
            return self.filter_function(input_text)
        else:
            logging.error("Neither of filter regex and filter functions are specified")


class IntNumberFilter(InputFilter):
    def __init__(self,
                 not_passed_reason_message: AnyStr = None):
        super().__init__(filter_regex=re.compile(r'[0-9]+'),
                         not_passed_reason_message=not_passed_reason_message)


class DoubleNumberFilter(InputFilter):
    def __init__(self,
                 not_passed_reason_message: AnyStr = None):
        super().__init__(filter_regex=re.compile(r'[0-9]+[,.][0-9]+'),
                         not_passed_reason_message=not_passed_reason_message)
