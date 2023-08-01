from __future__ import annotations
import sys
from typing import List, AnyStr, Optional, Callable, Union
from telegram.parsemode import ParseMode
from typing_module_extensions.instance_or_callable import InstanceOrCallable
from os.path import exists
import hashlib
import requests


class MessagePicture:
    def __init__(self,
                 picture_file_disk_source: Optional[AnyStr] = None,
                 picture_file_telegram_id: Optional[AnyStr] = None,
                 picture_file_link: Optional[AnyStr] = None):
        if picture_file_disk_source is None and picture_file_telegram_id is None and picture_file_link is None:
            raise ValueError('File disk source and file telegram id and photo link cannot both be none')
        self.picture_file_disk_source = picture_file_disk_source
        self.picture_file_telegram_id = picture_file_telegram_id
        self.picture_file_link = picture_file_link

    def get_picture_source(self):
        if self.picture_file_link is not None:  # Телеграм плохо работает (работает ли вообще?) с web link на image, поэтому закачиваем изображение к себе
            link_hash = hashlib.md5(str.encode(self.picture_file_link)).hexdigest()
            file_disc_source = 'resources/temp_image{0}.jpg'.format(link_hash)
            if not exists(file_disc_source):
                img_data = requests.get(self.picture_file_link).content
                with open(file_disc_source, 'wb') as handler:
                    handler.write(img_data)
            return file_disc_source
        return self.picture_file_disk_source or self.picture_file_telegram_id


class MessageKeyboardButton:
    def __init__(self,
                 text: AnyStr | Callable[..., AnyStr],
                 actions: 'Optional[List[Action] | Callable[..., List[Action]] | '
                          'List[Callable[..., Action]] | Callable[..., List[Callable[..., Action]]]]' = None):
        self._text = InstanceOrCallable(text)
        self._actions = InstanceOrCallable(actions)

    def get_text(self,
                 scope: 'Scope',
                 user: 'User') -> AnyStr:
        return self._text.get(scope, user)

    def get_actions(self,
                    scope,
                    user) -> 'List[Action]':
        return self._actions.get(scope, user) or []


class MessageKeyboard:

    def __init__(self,
                 buttons: List[MessageKeyboardButton | Callable[..., MessageKeyboardButton]] | Callable[..., List[MessageKeyboardButton | Callable[..., MessageKeyboardButton]]],
                 buttons_layout: Optional[List[int]] = None,
                 is_non_keyboard_input_allowed: bool = False,
                 is_inline_keyboard: bool = False):
        self._buttons = InstanceOrCallable(buttons)
        self._buttons_layout = buttons_layout or [sys.maxsize]  # Если не указан layout для кнопок - располагаем в одну строчку.
        self.is_non_keyboard_input_allowed = is_non_keyboard_input_allowed
        self.is_inline_keyboard = is_inline_keyboard

    def get_buttons(self,
                    scope: 'Scope',
                    user: 'User',
                    keyboard_type: AnyStr = "reply") -> List[List[MessageKeyboardButton]]:
        buttons = [InstanceOrCallable(button).get(scope, user) for button in self._buttons.get(scope, user)]
        buttons_layout = []
        current_button_index = 0
        current_layout_row_index = 0
        while current_button_index < len(buttons) and current_layout_row_index < len(self._buttons_layout):
            count_of_buttons_to_add = min(len(buttons) - current_button_index,
                                          self._buttons_layout[current_layout_row_index])
            buttons_layout.append(buttons[current_button_index: current_button_index + count_of_buttons_to_add])
            current_layout_row_index += 1
            current_button_index += count_of_buttons_to_add
        return buttons_layout


class Message:

    def __init__(self,
                 text: Optional[AnyStr | Callable[..., AnyStr]] = None,
                 text_parse_mode: ParseMode | Callable[..., ParseMode] = ParseMode.HTML,
                 picture: Optional[MessagePicture | Callable[..., MessagePicture]] = None,
                 keyboard: Optional[MessageKeyboard | Callable[..., MessageKeyboard]] = None,
                 should_replace_last_message: bool | Callable[..., bool] = False,
                 should_delete_last_message: bool | Callable[..., bool] = False,
                 text_processor_method: Callable[..., Optional[AnyStr]] | Callable[..., Callable[..., Optional[AnyStr]]] = lambda text: text):  # Функция, применяемая нвд динамическим текстом после его рендера.
        self._text = InstanceOrCallable(text)
        self._text_parse_mode = InstanceOrCallable(text_parse_mode)
        self._picture = InstanceOrCallable(picture)
        self._keyboard = InstanceOrCallable(keyboard)
        self._should_replace_last_message = InstanceOrCallable(should_replace_last_message)
        self._should_delete_last_message = InstanceOrCallable(should_delete_last_message)
        self._text_processor_method = InstanceOrCallable(text_processor_method)

    def get_text(self,
                 scope: 'Scope',
                 user: 'User') -> Optional[AnyStr]:
        text_processor_method = self._get_text_processor_method(scope, user)
        self.set_onetime_text_processor_method(lambda text: text)  # TextProcessorMethod одноразовый, поэтому возвращаем после единичного использования.
        return text_processor_method(self._text.get(scope, user))

    def get_text_parse_mode(self,
                            scope: 'Scope',
                            user: 'User') -> ParseMode:
        return self._text_parse_mode.get(scope, user)

    def _get_text_processor_method(self,
                                   scope: 'Scope',
                                   user: 'User') -> Callable[..., Optional[AnyStr]]:
        return self._text_processor_method.get(scope, user)

    def set_onetime_text_processor_method(self,
                                          text_processor_method: Callable[..., Optional[AnyStr]] | Callable[..., Callable[..., Optional[AnyStr]]]):
        self._text_processor_method = InstanceOrCallable(text_processor_method)

    def get_picture(self,
                    scope: 'Scope',
                    user: 'User') -> Optional[MessagePicture]:
        return self._picture.get(scope, user)

    def get_keyboard(self,
                     scope: 'Scope',
                     user: 'User') -> Optional[MessageKeyboard]:
        return self._keyboard.get(scope, user)
    
    def should_delete_last_message(self,
                                   scope: 'Scope',
                                   user: 'User') -> bool:
        return self._should_delete_last_message.get(scope, user)

    def should_replace_last_message(self,
                                   scope: 'Scope',
                                   user: 'User') -> bool:
        return self._should_replace_last_message.get(scope, user)
