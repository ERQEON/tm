import telebot
import random
import json
import os
import time
from telebot import types
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEH = os.getenv('BOT_TOKEH')

bot = telebot.TeleBot(BOT_TOKEH)

FILE_NAME = "data.json"

@bot.message_handler(commands=['start'])
def welcome(message):
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("Добавить в группу", url="https://t.me/twitchmetrbot?startgroup")
    markup.add(btn)
    bot.send_message(message.chat.id, "TwitchMetr - функционален только в группе", reply_markup=markup)

@bot.message_handler(commands=['play'])
@bot.message_handler(func=lambda message: message.text.lower() == 'стрим')
def stream(message):
    if message.chat.type in ['group', 'supergroup']:
        chat_id = str(message.chat.id)
        user_id = str(message.from_user.id)
        user_name = message.from_user.first_name
        current_time = time.time()
        num = random.randint(1, 50)

        if os.path.exists(FILE_NAME):
            with open(FILE_NAME, "r", encoding="utf=8") as f:
                try:
                    all_data = json.load(f)
                
                except json.JSONDecodeError:
                    all_data = {}
        else:
            all_data = {}
        
        chat_data = all_data.get(chat_id, {})
        user_info = chat_data.get(user_id, {"followers": 0, "last_stream": 0})

        last_stream = user_info.get("last_stream", 0)
        time_passed = current_time - last_stream

        if time_passed < 1800:
            minutes_left = int((1800 - time_passed) // 60)
            markup = types.InlineKeyboardMarkup()
            btn = types.InlineKeyboardButton("Добавить в группу", url="https://t.me/twitchmetrbot?startgroup")
            markup.add(btn)
            bot.send_message(message.chat.id, f"{user_name}, повтори попытку через: {minutes_left}м.", reply_markup=markup)
            return

        user_total = chat_data.get(user_id, 0)
        new_total = user_info["followers"] + num

        if new_total < 0: new_total = 0
        
        chat_data[user_id] = {
            "followers": new_total,
            "last_stream": current_time
        }
        all_data[chat_id] = chat_data

        status = f"+{num}" if num >= 0 else f"😬 Упс... {num}"
        
        with open(FILE_NAME, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=4)    
            
        bot.send_message(message.chat.id, f"{user_name}, ты запустил стрим.\n{status} фолловеров\n\nУ тебя всего {new_total} фолловеров!")

    else:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("Добавить в группу", url="https://t.me/twitchmetrbot?startgroup")
        markup.add(btn)
        bot.send_message(message.chat.id, "TwitchMetr - функционален только в группе", reply_markup=markup)

bot.polling(none_stop=True)