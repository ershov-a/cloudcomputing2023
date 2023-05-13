import logging

import telebot
import json
import os
import feedparser
import requests
import openai
import pyqrcode
import png
import ydb
import ydb.iam

from pyowm.owm import OWM
from telebot import types
from telebot.types import ReplyKeyboardRemove
from pycbrf.toolbox import ExchangeRates
from datetime import date
from openai.error import RateLimitError, InvalidRequestError
from requests.exceptions import ReadTimeout

API_TOKEN = os.environ['TELEGRAM_TOKEN']
OWM_TOKEN = os.environ['OWM_TOKEN']
FEEDBACK_GROUP_ID = os.environ['FEEDBACK_GROUP_ID']
GPT_TOKEN = os.environ['GPT_TOKEN']

# GPT key
openai.api_key = GPT_TOKEN

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)

bot = telebot.TeleBot(API_TOKEN, threaded=False)

# YDB conection
# Create driver in global space.
driver = ydb.Driver(
    endpoint=os.getenv('YDB_ENDPOINT'),
    database=os.getenv('YDB_DATABASE'),
    credentials=ydb.iam.MetadataUrlCredentials(),
)

# Wait for the driver to become active for requests.
driver.wait(fail_fast=True, timeout=5)

# Create the session pool instance to manage YDB sessions.
pool = ydb.SessionPool(driver)


# Increment specified command usage count
def update_cmd_stats(cmd):
    def execute_query(session):
        # Create the transaction and execute query
        query = "UPDATE stats SET usecount = usecount + 1 WHERE command = '%s'" % cmd
        return session.transaction().execute(
            query,
            commit_tx=True,
            settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2)
        )

    result = pool.retry_operation_sync(execute_query)


def process_event(event):
    request_body_dict = json.loads(event['body'])
    update = telebot.types.Update.de_json(request_body_dict)
    bot.process_new_updates([update])


def handler(event, context):
    process_event(event)
    return {
        'statusCode': 200
    }


# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, "Hi, I am Info service bot. Check available commands with menu button")


# Handle '/brief'
# with mock answer
@bot.message_handler(commands=['brief'])
def mock_message(message):
    update_cmd_stats("mock")
    bot.reply_to(message, "Feature in development, try again later")


# Handle '/weather'
@bot.message_handler(commands=['weather'])
def weather_message(message):
    update_cmd_stats("weather")

    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    button_geo = types.KeyboardButton(text="Send current location", request_location=True)
    keyboard.add(button_geo)
    msg = bot.send_message(message.chat.id, "[Only for mobile clients]\n"
                                            "Send current location with button below or "
                                            "any other location - tap paperclip icon, then tap on the Location",
                           reply_markup=keyboard)
    bot.register_next_step_handler(msg, weather_handle)


def weather_handle(message):
    if message.location is not None:
        # Get weather from OpenWeatherMap
        owm = OWM(OWM_TOKEN)
        mgr = owm.weather_manager()
        current_weather = mgr.weather_at_coords(lat=message.location.latitude, lon=message.location.longitude)
        # Assemble the message
        reply_str = "It's "
        reply_str += current_weather.weather.detailed_status + ", "
        # Convert from Kelvin to Celsius
        reply_str += str(round(current_weather.weather.temp.get('temp') - 273.15, 1)) + "°C"
        reply_str += ", and " + str(current_weather.weather.humidity) + "% humidity "
        reply_str += "in " + current_weather.location.name
        reply_str += ' (country code ' + current_weather.location.country + ") "
        reply_str += "now"
        # Send assembled message
        bot.reply_to(message, reply_str, reply_markup=ReplyKeyboardRemove())
    else:
        bot.reply_to(message, "Sorry, this is not a location. Try again", reply_markup=ReplyKeyboardRemove())


# Handle '/news'
@bot.message_handler(commands=['news'])
def news_message(message):
    update_cmd_stats("news")

    keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    button_cnews = types.KeyboardButton(text="CNews")
    keyboard.add(button_cnews)
    button_habr = types.KeyboardButton(text="Habr")
    keyboard.add(button_habr)
    button_opennet = types.KeyboardButton(text="OpenNET")
    keyboard.add(button_opennet)

    msg = bot.send_message(message.chat.id, "Select news source", reply_markup=keyboard)
    bot.register_next_step_handler(msg, news_handle)


def news_handle(message):
    match message.text:
        case "CNews":
            news_feed = feedparser.parse("https://www.cnews.ru/inc/rss/news_top.xml")
            bot.reply_to(message, get_news(news_feed), reply_markup=ReplyKeyboardRemove())
        case "Habr":
            news_feed = feedparser.parse("https://habr.com/ru/rss/news/?fl=ru")
            bot.reply_to(message, get_news(news_feed), reply_markup=ReplyKeyboardRemove())
        case "OpenNET":
            news_feed = feedparser.parse("https://www.opennet.ru/opennews/opennews_6_noadv.rss")
            bot.reply_to(message, get_news(news_feed), reply_markup=ReplyKeyboardRemove())
        case _:
            bot.reply_to(message, "Sorry, wrong news feed selected. Try again", reply_markup=ReplyKeyboardRemove())


def get_news(news_feed):
    news = 'Last 10 news: \n'
    for i in range(10):
        entry = news_feed.entries[i]
        news += '\n- ' + entry.title + '\n' + entry.link + '\n'
    return news


# Handle '/currencies'
def get_rate_cbr(currency_code):
    today = date.today()
    rates = ExchangeRates(str(today))
    return round(float(rates[currency_code].rate), 2)


def get_rate_for_symbol_binance(symbol):
    # request url
    url = "https://api.binance.com/api/v3/ticker/price?symbol=" + symbol
    # request data from url
    data = requests.get(url)
    data = data.json()
    return round(float(data['price']), 2)


@bot.message_handler(commands=['currencies'])
def feedback_message(message):
    update_cmd_stats("currencies")

    msg = "Currencies rates (CBR):\n"
    msg += "- USD " + str(get_rate_cbr("USD")) + "\n"
    msg += "- EUR " + str(get_rate_cbr("EUR")) + "\n"
    msg += "- CNY " + str(get_rate_cbr("CNY")) + "\n"
    msg += "Cryptocurrencies rates:\n"
    msg += "- ETH/USDT " + str(get_rate_for_symbol_binance("ETHUSDT")) + "\n"
    msg += "- BTC/USDT " + str(get_rate_for_symbol_binance("BTCUSDT")) + "\n"

    bot.reply_to(message, msg)


# Handle '/gpt'
def gpt_check_length(answer, list_of_answers):
    if 4090 < len(answer) < 409000:
        list_of_answers.append(answer[0:4090] + "...")
        gpt_check_length(answer[4091:], list_of_answers)
    else:
        list_of_answers.append(answer[0:])
        return list_of_answers


def gpt_make_request(message):
    try:
        engine = "text-davinci-003"
        completion = openai.Completion.create(
            engine=engine,
            prompt=message.text,
            temperature=0.5,
            max_tokens=3100,
        )
        list_of_answers = gpt_check_length(completion.choices[0]["text"], [])
        if list_of_answers:
            for piece_of_answer in list_of_answers:
                bot.send_message(message.chat.id, piece_of_answer)
        else:
            gpt_make_request(message)
    except (RateLimitError, ReadTimeout):
        bot.send_message(
            message.chat.id,
            "ChatGPT is overloaded, try again later",
        )
    except InvalidRequestError:
        bot.send_message(
            message.chat.id,
            "The maximum length of the context 3000 words, the answer exceeded the length of the context. Repeat the "
            "question or rephrase it",
        )


@bot.message_handler(commands=['gpt'])
def gpt_message(message):
    update_cmd_stats("gpt")

    msg = bot.send_message(message.chat.id, "Send message for ChatGPT")
    bot.register_next_step_handler(msg, gpt_handle)


def gpt_handle(message):
    gpt_make_request(message)


# Handle '/generate_qr_code'
@bot.message_handler(commands=['generate_qr_code'])
def qr_code_handler(message):
    update_cmd_stats("generate_qr_code")
    sent = bot.send_message(message.chat.id, "Answer this message with text or link to generate a qr code")
    bot.register_next_step_handler(sent, qrcode)


def qrcode(message):
    qr_file = f'/tmp/{message.message_id}.png'
    try:
        url = pyqrcode.create(message.text)
        url.png(qr_file, scale=15)
        bot.send_chat_action(message.chat.id, 'upload_document')
        bot.send_document(message.chat.id, reply_to_message_id=message.message_id, document=open(qr_file, 'rb'),
                          caption="Here is your QR code", visible_file_name="qr.png")
        os.remove(qr_file)
    except Exception:
        bot.reply_to(message, "An error occurred, try again")


# Handle '/feedback'
@bot.message_handler(commands=['feedback'])
def feedback_message(message):
    update_cmd_stats("feedback")
    msg = bot.reply_to(message, "Send the message to be sent to the developer")
    bot.register_next_step_handler(msg, feedback_handle)


def feedback_handle(message):
    bot.reply_to(message, "Your message was sent to the developer")
    bot.send_message(FEEDBACK_GROUP_ID, "Feedback from " + message.from_user.username + ", text: " + message.text)


# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
def echo_message(message):
    update_cmd_stats("unrecognized_commands")
    bot.reply_to(message, 'Command not recognised, check syntax.')
