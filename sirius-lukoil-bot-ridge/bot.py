import logging
import os
from types import SimpleNamespace
from typing import AnyStr

import telegram.error
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update, InputMediaPhoto, ReplyKeyboardRemove
from telegram.ext import MessageHandler, Filters, Updater, CallbackQueryHandler, CallbackContext
from telegram.replykeyboardmarkup import ReplyKeyboardMarkup

from data_access_layer.google_tables import SheetsClient
from global_transferable_entities.scope import Scope
from global_transferable_entities.user import User


class Bot:

    def __init__(self,
                 token: AnyStr,
                 scope: Scope):
        self._token = token
        self._updater = Updater(token)
        self._dispatcher = self._updater.dispatcher
        self._bot = self._updater.bot
        self._scope = scope

        self._dispatch()

    def _dispatch(self):
        callback_handler = CallbackQueryHandler(self.process_callback)
        message_handler = MessageHandler(Filters.text | Filters.command, self.process_message)
        self._dispatcher.add_handler(message_handler)
        self._dispatcher.add_handler(callback_handler)
        logging.info("Bot dispatched")

    def start_polling(self,
                      poll_interval=5,
                      poll_timeout=3):
        self._updater.start_polling(poll_interval=poll_interval,
                                    timeout=poll_timeout)
        logging.info('Bot polling started')

    def start_webhook(self,
                      port,
                      server_ip,
                      sertificate_path,
                      key_path):
        webhook_url = 'https://{}:{}/{}'.format(server_ip,
                                                port,
                                                self._token)
        logging.info("Set webhook with url : {}".format(webhook_url))
        self._updater.start_webhook(listen='127.0.0.1',
                                    port=port,
                                    url_path=self._token,
                                    cert=sertificate_path,
                                    key=key_path,
                                    webhook_url=webhook_url)
        self._updater.idle()

    def process_callback(self,
                         update: Update):
        try:
            username = update.message.chat.username
        except Exception:
            username = ""
        update.message = SimpleNamespace()
        update.message.chat = SimpleNamespace()
        update.message.chat.username = username
        update.message.text = update.callback_query.data
        self.process_message(update)

        update.callback_query.answer()

    def process_message(self,
                        update: Update,
                        context: CallbackContext = None,
                        fake_process: bool = False):  # При fake_process не нужно выполнять actions этапа. TODO: Найти способ изящнее, если ошибка при отправке сообщения.
        bot = context.bot if context is not None else self._bot

        update = update

        update_text = update.message.text
        user_chat_id = update.effective_chat.id

        logging.info("-" * 50)
        logging.info("Обрабатываю сообщение пользователя с id = {}".format(user_chat_id))
        logging.info("Текст сообщения = {}".format(update_text))

        user = User(user_chat_id, update.message.chat.username)

        # Global command handler

        if self.global_command_handler(update_text, self._scope, user):

            return

        # Get current stage

        current_user_stage = self._scope.get_stage(user.get_current_stage_name())

        # Statistics

        current_user_stage.count_statistics(update_text, self._scope, user, current_user_stage)
        user.count_statistics(update_text, self._scope, user, current_user_stage)

        # Reply message

        if fake_process:
            transition_stage_message = self._scope.get_stage(user.get_current_stage_name()).get_message(self._scope, user)
        else:
            transition_stage_message = current_user_stage.process_input(update_text, self._scope, user, bot)

        transition_stage_message_text = transition_stage_message.get_text(self._scope, user)
        transition_stage_message_text_parse_mode = transition_stage_message.get_text_parse_mode(self._scope, user)
        transition_stage_message_keyboard = transition_stage_message.get_keyboard(self._scope, user)
        transition_stage_message_picture = transition_stage_message.get_picture(self._scope, user)

        message_reply_markup = self._get_reply_markup(transition_stage_message_keyboard, user)

        try:

            if transition_stage_message.should_delete_last_message(self._scope, user):
                try:
                    self._bot.delete_message(chat_id=user_chat_id,
                                               message_id=user.get_variable("_last_sent_message_id"))
                except telegram.error.BadRequest:  # Если сообщение, которое удаляем "протухло", то игнорируем удаление.
                    pass

            if transition_stage_message_picture is not None:
                if transition_stage_message.should_replace_last_message(self._scope, user):

                    try:
                        message = self._bot.edit_message_media(chat_id=user_chat_id,
                                                                 message_id=user.get_variable("_last_sent_message_id"),
                                                                 media=InputMediaPhoto(
                                                                     open(
                                                                         transition_stage_message_picture.get_picture_source(),
                                                                         'rb')),
                                                                 reply_markup=message_reply_markup)

                        message = self._bot.edit_message_caption(chat_id=user_chat_id,
                                                                   message_id=user.get_variable("_last_sent_message_id"),
                                                                   caption=transition_stage_message_text,
                                                                   reply_markup=message_reply_markup)
                    except Exception:
                        message = self._bot.send_photo(chat_id=user_chat_id,
                                                         photo=open(transition_stage_message_picture.get_picture_source(),
                                                                    'rb'),
                                                         caption=transition_stage_message_text,
                                                         parse_mode=transition_stage_message_text_parse_mode,
                                                         reply_markup=message_reply_markup)

                else:
                    message = self._bot.send_photo(chat_id=user_chat_id,
                                                     photo=open(transition_stage_message_picture.get_picture_source(),
                                                                'rb'),
                                                     caption=transition_stage_message_text,
                                                     parse_mode=transition_stage_message_text_parse_mode,
                                                     reply_markup=message_reply_markup)
            else:
                message = self._bot.send_message(chat_id=user_chat_id,
                                                   text=transition_stage_message_text,
                                                   parse_mode=transition_stage_message_text_parse_mode,
                                                   reply_markup=message_reply_markup)
            user.set_variable("_last_sent_message_id", message.message_id)

            prerequisite_actions = self._scope.get_stage(user.get_current_stage_name()).get_prerequisite_actions(self._scope, user)
            for prerequisite_action in prerequisite_actions:
                prerequisite_action.apply(self._scope, user, message)

            # Если этап на котором оказался пользователь - проходная, то сразу обрабатываем его и переходим к следующему.
            if self._scope.get_stage(user.get_current_stage_name()).is_gatehouse():
                self.process_message(update)

        except Exception as e:
            # При этом действия на этапе не выполняем! Поэтому fake_process. Выполняем только send_message_error_actions.
            logging.error("Не получилось отправить сообщение. Получил ошибку с текстом = {}. Пропускаю этап.".format(e))
            self._scope.get_stage(user.get_current_stage_name()).process_sending_message_error_actions(self._scope, user, context.bot)
            self.process_message(update,
                                 True)


    def _get_reply_markup(self,
                          transition_stage_message_keyboard,
                          user):
        if transition_stage_message_keyboard is None:
            return ReplyKeyboardRemove()  # Если клавиатуры нет, убираем существующую.
        else:
            keyboard_buttons = transition_stage_message_keyboard.get_buttons(self._scope, user)
            keyboard_buttons_strings = [[button.get_text(self._scope, user) for button in keyboard_buttons_line] for
                                        keyboard_buttons_line in keyboard_buttons]

            if transition_stage_message_keyboard.is_inline_keyboard:
                return InlineKeyboardMarkup([list(map(lambda button: InlineKeyboardButton(button,
                                                                                          callback_data=button),
                                                      keyboard_buttons_string_line)) for keyboard_buttons_string_line in keyboard_buttons_strings],
                                            resize_keyboard=True,
                                            one_time_keyboard=True)
            else:
                return ReplyKeyboardMarkup(keyboard_buttons_strings,
                                           resize_keyboard=True,
                                           one_time_keyboard=True)

    def global_command_handler(self,
                               text: AnyStr,
                               scope: Scope,
                               user: User):
        if text == "kill":
            user.delete()
            return True
        if text == "/start":
            user.change_stage("NewUser")  # Команда start принудительно обновляет этап юзера, но продолжает исполнение, эмулируя удаление пользователя.
        if text == "info":
            self._bot.send_message(chat_id=user.chat_id,
                                     text="Ваш chat_id : {}".format(user.chat_id))
            return True
        if text == "sync":
            SheetsClient(os.environ['sheets_token']).synchronize()
            worker = Worker()
            worker.generate_goods_files()
            self._bot.send_message(chat_id=user.chat_id,
                                     text="Таблица была успешно синхронизирована с google tables")
            return True
        if text == "bsync":
            SheetsClient(os.environ['sheets_token']).back_synchronize()
            self._bot.send_message(chat_id=user.chat_id,
                                     text="Таблица была успешно обратно синхронизирована с google tables")
        return False
