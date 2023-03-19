import telebot
import logging
import os

with open(os.path.dirname(os.path.realpath(__file__)) + '/.env') as file:
    API_TOKEN = file.readline().strip()

bot = telebot.TeleBot(API_TOKEN)

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', filename="log.txt", level=logging.DEBUG,
                    datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger('TeleBot').setLevel(logging.DEBUG)


# Handle '/start' and '/help'
@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, """\
Hi, I am Info service bot.
Check available commands with menu button.\
""")


# Handle '/weather', '/currencies', '/news', '/brief', '/feedback'
# with mock answer
@bot.message_handler(commands=['weather', 'currencies', 'news', 'brief'])
def mock_message(message):
    bot.reply_to(message, """\
Feature in development, try again later.\
""")


@bot.message_handler(commands=['feedback'])
def mock_message(message):
    msg = bot.reply_to(message, """\
Send the message to be sent to the developer:\
""")
    bot.register_next_step_handler(msg, feedback_handle)


def feedback_handle(message):
    logging.info('Feedback from username %s: %s', message.from_user.username, message.text)
    bot.reply_to(message, """\
   Message sent.\
   """)


# Handle all other messages with content_type 'text' (content_types defaults to ['text'])
@bot.message_handler(func=lambda message: True)
def echo_message(message):
    bot.reply_to(message, 'Command not recognised, check syntax.')


bot.infinity_polling()
