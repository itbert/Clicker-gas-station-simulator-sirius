import json
import os
import sqlite3
import logging
from sqlite3 import Connection, Cursor
from typing import List
import mysql.connector

class Database:
    _cur: Cursor = None
    _con: Connection = None


    @staticmethod
    def _connect(local_db: bool = True):
        if local_db:
            Database._con = sqlite3.connect("database.sqlite", check_same_thread=False)
            Database._con.row_factory = sqlite3.Row
            Database._cur = Database._con.cursor()
        else:
            Database._con = mysql.connector.connect(
                host="localhost",
                user=os.environ['mysql_login'],
                password=os.environ['mysql_password'],
                database=os.environ['mysql_db'])
            Database._con.row_factory = sqlite3.Row
            Database._cur = Database._con.cursor(dictionary=True)

    @staticmethod
    def _run(query,
             params: List = None,
             need_save: bool = False,
             try_number: int = 1):

        if Database._con is None:
            Database._connect()

        logging.info('DB request: {}'.format(query))

        if params is not None:
            if isinstance(params, list):
                logging.info('DB params: {}'.format(','.join(str(param) for param in params)))
            else:
                logging.info('DB params: {}'.format(str(params)))

        try:
            if params is not None:
                Database._cur.execute(query, params)
                answer = Database._cur.fetchall()
            else:
                Database._cur.execute(query)
                answer = Database._cur.fetchall()

            if need_save or query.find('update') != -1 or query.find('insert') != -1 or query.find('delete') != -1:
                Database._con.commit()

            logging.info('DB answer rows count: '.format(len(answer)))

            return answer
        except Exception as exeption:
            if try_number > 1:
                logging.error("Database problem. More than one reconnecting try was force ended.")
            else:
                logging.warning("Database possible problem. Exception is {}. Trying to reconnect...".format(exeption))

            Database._connect()
            Database._run(query, params, need_save)

    # Commands:

    @staticmethod
    def is_user_exist(chat_id: str) -> bool:
        data = Database._run("select * from users where chat_id = ?", (chat_id,))
        return len(data) > 0

    @staticmethod
    def add_user(chat_id: str,
                 stage_history: List[str],
                 user_variables: dict):
        stage_history_json = json.dumps(stage_history)
        user_variables_json = json.dumps(user_variables)
        Database._run("insert into users(chat_id, stage_history, user_variables) values (?, ?, ?)",
                      (chat_id, stage_history_json, user_variables_json))

    @staticmethod
    def get_user(chat_id: str) -> dict:
        data = Database._run("select * from users where chat_id = ?", (chat_id,))
        if len(data) > 0:
            user_from_db = data[0]
            user_from_db_dict = {'stage_history': json.loads(user_from_db['stage_history']),
                                 'user_variables': json.loads(user_from_db['user_variables'])}
            return user_from_db_dict
        else:
            return {}

    @staticmethod
    def delete_user(chat_id: str):
        Database._run("delete from users where chat_id = ?", (chat_id,))

    @staticmethod
    def change_user_column(chat_id: str, column_name: str, column_value: object):
        if isinstance(column_value, list) or isinstance(column_value, dict):
            column_value = json.dumps(column_value)

        data = Database._run("update users set {} = ? where chat_id = ?".format(column_name), (column_value, chat_id))

    @staticmethod
    def get_scope() -> dict:
        data = Database._run("select * from scopes")
        if len(data) > 0:
            scope_from_db = data[0]
            scope_from_db_dict = {'global_variables': json.loads(scope_from_db['global_variables'])}
            return scope_from_db_dict
        else:
            return {}

    @staticmethod
    def change_scope_column(column_name: str, column_value: object):
        if isinstance(column_value, list) or isinstance(column_value, dict):
            column_value = json.dumps(column_value)

        data = Database._run("update scopes set {} = ?".format(column_name), (column_value,))
