import telebot
import logging
import os
from pyowm.owm import OWM
from telebot import types
from telebot.types import ReplyKeyboardRemove

with open(os.path.dirname(os.path.realpath(__file__)) + '/.env') as file:
    API_TOKEN = file.readline().strip()
    OWM_TOKEN = file.readline().strip()
    FEEDBACK_GROUP_ID = file.readline().strip()

bot = telebot.TeleBot(API_TOKEN)

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', filename="log.txt", level=logging.DEBUG,
                    datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger('TeleBot').setLevel(logging.DEBUG)


# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, "Hi, I am Info service bot. Check available commands with menu button")


# Handle '/currencies', '/news', '/brief', '/feedback'
# with mock answer
@bot.message_handler(commands=['currencies', 'news', 'brief'])
def mock_message(message):
    bot.reply_to(message, "Feature in development, try again later")


# Handle '/weather'
@bot.message_handler(commands=['weather'])
def weather_message(message):
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


@bot.message_handler(commands=['feedback'])
def feedback_message(message):
    msg = bot.reply_to(message, "Send the message to be sent to the developer")
    bot.register_next_step_handler(msg, feedback_handle)


def feedback_handle(message):
    bot.reply_to(message, "Your message was sent to the developer")
    bot.send_message(FEEDBACK_GROUP_ID, "Feedback from " + message.from_user.username + ", text: " + message.text)


# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
def echo_message(message):
    bot.reply_to(message, 'Command not recognised, check syntax.')


bot.infinity_polling()
