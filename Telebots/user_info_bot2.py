import telebot
import json
import os

bot = telebot.TeleBot("6911832256:AAFAtYPiLmL0TP7jFn6jZB_iFiAac0nWFV4")

chat_state = {}

def load_data():
    if os.path.exists('db.json'):
        with open('db.json', 'r') as infile:
            return json.load(infile) if os.stat('db.json').st_size != 0 else {"chats_configuration": {}}
    return {"chats_configuration": {}}

def save_data(data):
    with open('db.json', 'w') as outfile:
        json.dump(data, outfile)

user_data = load_data()

def reset_state(chat_id):
    chat_state[chat_id] = 'ASK_NAME'

@bot.message_handler(commands=['start'])
def start_bot(message):
    reset_state(message.chat.id)
    ask_name(message)

def ask_name(message):
    bot.send_message(message.chat.id, "Привет, я бот опросник. Хочу задать тебе несколько вопросов.\nКак тебя зовут?")
    chat_state[message.chat.id] = 'ASK_AGE'

def ask_age(message):
    name = message.text
    if name.startswith('/') or name.isdigit():
        bot.send_message(message.chat.id, "Пожалуйста, введите ваше имя без символа '/' и чисел.")
    else:
        user_data['chats_configuration'][str(message.chat.id)] = {'name': name}
        bot.send_message(message.chat.id, f"Приятно познакомиться, {name}. Сколько тебе лет?")
        chat_state[message.chat.id] = 'ASK_CITY'

def ask_city(message):
    age = message.text
    if not age.isdigit():
        bot.send_message(message.chat.id, "Пожалуйста, введите ваш возраст числом.")
    else:
        user_data['chats_configuration'][str(message.chat.id)]['age'] = age
        bot.send_message(message.chat.id, "Отлично! Из какого ты города?")
        chat_state[message.chat.id] = 'VALIDATE_CITY'

def validate_city(message):
    city = message.text
    if not city.replace(' ', '').replace('-', '').isalpha():
        bot.send_message(message.chat.id, "Пожалуйста, введите название города буквами.")
    else:
        user_data['chats_configuration'][str(message.chat.id)]['city'] = city
        bot.send_message(message.chat.id, "Прекрасно. Можешь отправить мне видеосообщение?")
        chat_state[message.chat.id] = 'CHECK_VIDEO'

@bot.message_handler(content_types=['video', 'video_note'])
def handle_video(message):
    if chat_state.get(message.chat.id) == 'CHECK_VIDEO':
        
        if message.content_type == 'video':
            file_info = bot.get_file(message.video.file_id)
        elif message.content_type == 'video_note':
            file_info = bot.get_file(message.video_note.file_id)
        
        downloaded_file = bot.download_file(file_info.file_path)
        video_filename = f"{message.chat.id}_{file_info.file_path.split('/')[-1]}"
        with open(video_filename, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        user_data['chats_configuration'][str(message.chat.id)]['video'] = video_filename
        save_data(user_data)
        
        bot.send_message(message.chat.id, "Спасибо за видеосообщение!")
        reset_state(message.chat.id)

@bot.message_handler(func=lambda message: chat_state.get(message.chat.id) == 'CHECK_VIDEO')
def handle_wrong_format(message):
    bot.send_message(message.chat.id, "Пожалуйста, отправьте сообщение в видеоформате.")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(message):
    if chat_state.get(message.chat.id) == 'ASK_AGE':
        ask_age(message)
    elif chat_state.get(message.chat.id) == 'ASK_CITY':
        ask_city(message)
    elif chat_state.get(message.chat.id) == 'VALIDATE_CITY':
        validate_city(message)

bot.polling()