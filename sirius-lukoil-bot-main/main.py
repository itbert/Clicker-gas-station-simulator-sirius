import telebot
import json
import datetime
import random
import hashlib

# Create a new bot by passing your bot token
bot = telebot.TeleBot("<PASTE_YOUR_TOKEN_HERE>")
data = {}


class UserData:
    def __init__(self, name, from_json=None):
        if from_json is None:
            self.name = name
            self.money = 0
            self.oil = 0
            self.towers = 0
            self.stations = 1
            self.workers = 0
            self.start_time = 0
            self.last_petrol_time = 0
            self.last_passive_earn_time = 0
            self.click_count = 0
            self.banned = False
            self.state = "StartScreen"
        else:
            self.name = from_json["name"]
            self.money = from_json["money"]
            self.oil = from_json["oil"]
            self.towers = from_json["towers"]
            self.stations = from_json["stations"]
            self.workers = from_json["workers"]
            self.start_time = from_json["start_time"]
            self.last_petrol_time = from_json["last_petrol_time"]
            self.last_passive_earn_time = from_json["last_passive_earn_time"]
            self.click_count = from_json["click_count"] if "click_count" in from_json else 0
            self.state = from_json["state"]
            self.banned = from_json["banned"]

    def as_json(self):
        return {
            "name": self.name,
            "money": self.money,
            "oil": self.oil,
            "towers": self.towers,
            "stations": self.stations,
            "workers": self.workers,
            "start_time": self.start_time,
            "last_petrol_time": self.last_petrol_time,
            "last_passive_earn_time": self.last_passive_earn_time,
            "click_count": self.click_count,
            "banned": self.banned,
            "state": self.state
        }

    def reset(self):
        self.money = 0
        self.oil = 0
        self.towers = 0
        self.stations = 1
        self.workers = 0
        self.start_time = 0
        self.last_petrol_time = 0
        self.last_passive_earn_time = 0
        self.state = "StartScreen"


# get current time in seconds
def get_current_time() -> float:
    return (datetime.datetime.utcnow()-datetime.datetime(1970,1,1)).total_seconds()


def get_user_name(user):
    if user.username is not None:
        return user.username
    return user.first_name + (" " + user.last_name) if user.last_name is not None else ""


def load_data():
    global data
    try:
        f = open("data.txt", "r", encoding="utf8")
        raw_data = json.loads(f.read())
        data = {}
        for k, v in raw_data.items():
            data[k] = UserData("", v)
        f.close()
    except FileNotFoundError:
        data = {}


def save_data():
    raw_data = {}
    for k, v in data.items():
        raw_data[k] = v.as_json()
    with open("data.txt", "w", encoding="utf8") as f:
        f.write(json.dumps(raw_data))


def reset_user_data(user: telebot.types.User):
    data[str(user.id)].reset()
    save_data()


def add_buttons(markup, text):
    for x in text:
        markup.add(telebot.types.KeyboardButton(x))


def get_work_button(user_data):
    if user_data.towers > 0:
        return "Съездить на мальдивы"
    elif user_data.click_count >= 50:
        return "Проверить заправку"
    return "Заправить машину"

SCREENS = {
    "StartScreen": ["Устроиться на работу"],
    "MainScreen": [get_work_button, "Продать нефть", "Магазин", "Топ игроков"],
    "ShopScreen": ["Купить заправку", "Купить вышку", "Нанять работника", "Назад"],
    "SellOil": [],
    "EnterPassword": []
}
STORY = """Вы недавно выпустились из университета и хотите найти работу. Вам приглянулось объявление на должность заправщика в компанию ПАО «Лукойл».  
«_Хотите найти стабильную работу с хорошим заработком и быстрым карьерным ростом? ПАО «Лукойл» ждет вас на должность заправщика!_»
"""
STATIONS_PRICE = [0, 1000, 2000, 3000, 10000, 10000, 10000, 10000]
WORKERS_PRICE = [0, 500, 750, 1000, 1500, 2000, 2000, 2000, 2000]


def set_screen(user_data, markup, screen):
    user_data.state = screen
    save_data()
    add_buttons(markup, [x(user_data) if callable(x) else x for x in SCREENS[screen]])


def format_info(user):
    user_data = data[str(user.id)]
    return f'💰 Баланс: {int(user_data.money)}$\n🛢 Нефть: {int(user_data.oil)} баррелей\n⛽ Заправки: {user_data.stations}\n🧑‍💻 Работники: {user_data.workers}\n🗼 Вышки: {user_data.towers}'


def recalculate_passive_income(user_data):
    current_time = get_current_time()
    per_min_station = 10 + user_data.stations ** 2 * 4
    if user_data.last_passive_earn_time == 0:
        user_data.money += per_min_station * user_data.stations
        user_data.oil += 1 * user_data.towers
        user_data.last_passive_earn_time = current_time
    else:
        needed_workers = 5 * user_data.stations
        increment_value = (current_time - user_data.last_passive_earn_time) / 60

        user_data.money += increment_value * per_min_station * user_data.stations * (user_data.workers / needed_workers)
        user_data.oil += increment_value * user_data.towers
        user_data.last_passive_earn_time = current_time
    save_data()


load_data()


# Define the on_receive_callback function that will handle incoming messages
@bot.message_handler(func=lambda message: True)
def on_receive_callback(message: telebot.types.Message):
    # load_data()
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    user = message.from_user

    if user is None:
        return
    elif str(user.id) not in data:
        data[str(user.id)] = UserData(get_user_name(user))
        reset_user_data(user)

    user_data = data[str(user.id)]
    current_time = get_current_time()

    if user_data.banned:
        return bot.send_message(message.chat.id, "Вы заблокированы")

    if user_data.state != "StartScreen":
        recalculate_passive_income(user_data)

    if user_data.state == "EnterPassword":
        entered_pass = message.text
        hash_str = str(user.id)
        if user_data.towers >= 4:
            hash_str += "3"
        elif user_data.towers > 0:
            hash_str += "2"
        else:
            hash_str += "1"
        password = hashlib.sha256(hash_str.encode()).hexdigest()[:4]
        if entered_pass == password:
            set_screen(user_data, markup, "MainScreen")
            if user_data.towers == 4:
                bot.send_message(message.chat.id,
                                 "🎉 Поздравляем, вы прошли игру, в качестве подарка дарим вам стикеры: https://t.me/addstickers/LukoilOilCam")
            else:
                bot.send_message(message.chat.id, "✅ Верный пароль, продолжайте.", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "❌ Неверный пароль")
        return
    elif message.text == "/start":
        reset_user_data(user)
        set_screen(user_data, markup, "StartScreen")
        bot.send_message(message.chat.id, STORY, reply_markup=markup, parse_mode="markdown")

        return
    elif message.text == "Устроиться на работу":
        if user_data.state != "StartScreen":
            return bot.send_message(message.chat.id, "Вы уже устроились на работу")
        set_screen(user_data, markup, "MainScreen")
        bot.send_message(message.chat.id, "Вы устроились на работу", reply_markup=markup)

        return
    elif message.text == "Магазин":
        if user_data.state == "StartScreen":
            return bot.send_message(message.chat.id, "Вы должны устроиться на работу")
        set_screen(user_data, markup, "ShopScreen")
        prices = f"Цены:\n\n" \
                 f"⛽ Купить заправку: {-1 if user_data.stations >= 8 else STATIONS_PRICE[user_data.stations]}$\n" \
                 f"🗼 Купить вышку: 15000$\n" \
                 f"🧑‍💻 Нанять работника: {-1 if user_data.stations > 8 else WORKERS_PRICE[user_data.stations]}$"
        bot.send_message(message.chat.id, prices, reply_markup=markup)

        return
    elif message.text == "Назад":
        if user_data.state == "StartScreen":
            return bot.send_message(message.chat.id, "Вы должны устроиться на работу")
        elif user_data.state == "ShopScreen":
            set_screen(user_data, markup, "MainScreen")
            bot.send_message(message.chat.id, format_info(user), reply_markup=markup)
    elif message.text == "Заправить машину":
        if user_data.state == "StartScreen":
            return bot.send_message(message.chat.id, "Вы должны устроиться на работу")
        if current_time - user_data.last_petrol_time < 1:
            return bot.send_message(message.chat.id, "Не так быстро")
        user_data.last_petrol_time = current_time
        earned_money = random.randint(12, 25)
        user_data.money += earned_money
        user_data.click_count += 1
        save_data()
        bot.send_message(message.chat.id, f"Вы заправили машину и получили {earned_money}$\n\n" + format_info(user), reply_markup=markup)

        if user_data.click_count == 50:
            set_screen(user_data, markup, "EnterPassword")
            bot.send_message(message.chat.id, "Вы переходите на уровень менджера, пройдете тест и введите пароль.\n\n@OilMiner_worker_bot", reply_markup=markup)
        return
    elif message.text == "Проверить заправку":
        if user_data.state == "StartScreen":
            return bot.send_message(message.chat.id, "Вы должны устроиться на работу")
        if current_time - user_data.last_petrol_time < 1:
            return bot.send_message(message.chat.id, "Не так быстро")
        user_data.last_petrol_time = current_time
        earned_money = random.randint(30, 50)
        user_data.money += earned_money
        user_data.click_count += 1
        save_data()
        bot.send_message(message.chat.id, f"Вы проверили заправку, вам начислена премия {earned_money}$\n\n" + format_info(user), reply_markup=markup)
    elif message.text == "Съездить на мальдивы":
        if user_data.state != "MainScreen":
            return
        if current_time - user_data.last_petrol_time < 1:
            return bot.send_message(message.chat.id, "Не так быстро")
        user_data.last_petrol_time = current_time
        earned_money = 0
        if random.randint(0, 10) >= 8:
            earned_money = random.randint(-100, -50)
            bot.send_message(message.chat.id, f"Вас обокрали, вы потеряли {-earned_money}$\n\n" + format_info(user), reply_markup=markup)
        else:
            earned_money = random.randint(50, 80)
            bot.send_message(message.chat.id, f"На отдыхе вы торговали акциями и заработали {earned_money}$\n\n" + format_info(user), reply_markup=markup)
        user_data.money += earned_money
        save_data()
    elif message.text == "Нанять работника":
        if user_data.state != "ShopScreen":
            return
        price = WORKERS_PRICE[user_data.stations]
        if user_data.stations * 5 <= user_data.workers:
            return bot.send_message(message.chat.id, f"У вас максимальное количество работников, купите больше заправок.", reply_markup=markup)
        if price > user_data.money:
            return bot.send_message(message.chat.id, f"Вам не хватает денег для найма работника. Необходимо {price} у вас {int(user_data.money)}.", reply_markup=markup)
        user_data.money -= price
        user_data.workers += 1
        save_data()
        return bot.send_message(message.chat.id, f"Вы наняли работника\n\n" + format_info(user), reply_markup=markup)
    elif message.text == "Купить заправку":
        if user_data.state != "ShopScreen":
            return
        if user_data.stations >= 8:
            return bot.send_message(message.chat.id, f"Вы купили максимальное количество заправок.")
        station_price = STATIONS_PRICE[user_data.stations]
        money = user_data.money
        if station_price > money:
            return bot.send_message(message.chat.id, f"У вас не хватает денег! Необходимо {station_price}$, у вас {int(money)}$.")
        user_data.money -= station_price
        user_data.stations += 1
        save_data()
        return bot.send_message(message.chat.id, f"Вы купили заправку.\n\n" + format_info(user), reply_markup=markup)
    elif message.text == "Купить вышку":
        if user_data.state != "ShopScreen":
            return
        if user_data.money < 15000:
            return bot.send_message(message.chat.id, f"У вас не хватает денег для покупки вышки. Необходимо 15000$, у вас {int(user_data.money)}$.", reply_markup=markup)

        user_data.towers += 1
        user_data.money -= 15000
        if user_data.towers == 1:
            # image here
            set_screen(user_data, markup, "EnterPassword")
            bot.send_message(message.chat.id,
                             "Поздравляем с покупкой первой вышки! Для перехода на уровень бизнесмена вы должны пройти тест, после прохождения теста вы получите пароль.\n\n@OilMinerBusiness_bot",
                             reply_markup=markup)
        elif user_data.towers == 4:
            set_screen(user_data, markup, "EnterPassword")
            bot.send_message(message.chat.id,
                             "Вы купили четвертую вышку и становитесь нефтебароном, после прохождения теста вы получите пароль.\n\n@OilBaronTest_bot",
                             reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Вы купили вышку", reply_markup=markup)

        save_data()
        return
    elif message.text == "Продать нефть":
        set_screen(user_data, markup, "SellOil")
        return bot.send_message(message.chat.id, f"Введите количество нефти, у вас {int(user_data.oil)}. Курс 1 баррель = 86$")
    elif user_data.state == "SellOil":
        try:
            oil = int(message.text)
            if user_data.oil < oil:
                set_screen(user_data, markup, "MainScreen")
                return bot.send_message(message.chat.id, "У вас не хватает нефти!", reply_markup=markup)
            user_data.oil -= oil
            user_data.money += 86 * oil
            save_data()
            set_screen(user_data, markup, "MainScreen")
            return bot.send_message(message.chat.id, f"Вы продали {oil} баррелей нефти и получили {86*oil}$")
        except:
            pass
    elif message.text == "Топ игроков":
        players = []
        for k in data.keys():
            recalculate_passive_income(data[k])
        for k, v in data.items():
            players.append((v.name, v.money))
        players = sorted(players, key=lambda x: x[1], reverse=True)
        text = "Топ-10 игроков:\n\n"
        for i in range(min(10, len(players))):
            text += f"{i+1}. {players[i][0]} - {int(players[i][1])}$\n"
        set_screen(user_data, markup, "MainScreen")
        return bot.send_message(message.chat.id, text, reply_markup=markup)



# Start the bot
bot.polling()