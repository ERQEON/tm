import telebot
import random
import time
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from telebot import types
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL') 

bot = telebot.TeleBot(BOT_TOKEN)

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS streams (
            chat_id TEXT,
            user_id TEXT,
            followers INTEGER DEFAULT 0,
            last_stream DOUBLE PRECISION DEFAULT 0,
            PRIMARY KEY (chat_id, user_id)
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

init_db()

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

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT followers, last_stream FROM streams WHERE chat_id = %s AND user_id = %s", (chat_id, user_id))
        user_info = cur.fetchone()

        if not user_info:
            user_info = {"followers": 0, "last_stream": 0}
        
        last_stream = user_info["last_stream"]
        time_passed = current_time - last_stream

        if time_passed < 1800:
            minutes_left = int((1800 - time_passed) // 60)
            markup = types.InlineKeyboardMarkup()
            btn = types.InlineKeyboardButton("Добавить в группу", url="https://t.me/twitchmetrbot?startgroup")
            markup.add(btn)
            bot.send_message(message.chat.id, f"{user_name}, повтори попытку через: {minutes_left}м.", reply_markup=markup)
            cur.close()
            conn.close()
            return

        new_total = user_info["followers"] + num
        if new_total < 0: new_total = 0

        cur.execute('''
            INSERT INTO streams (chat_id, user_id, followers, last_stream)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (chat_id, user_id) 
            DO UPDATE SET 
                followers = EXCLUDED.followers,
                last_stream = EXCLUDED.last_stream
        ''', (chat_id, user_id, new_total, current_time))

        conn.commit()
        cur.close()
        conn.close()

        status = f"+{num}" if num >= 0 else f"😬 Упс... {num}"
        bot.send_message(message.chat.id, f"{user_name}, ты запустил стрим.\n{status} фолловеров\n\nУ тебя всего {new_total} фолловеров!")

    else:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("Добавить в группу", url="https://t.me/twitchmetrbot?startgroup")
        markup.add(btn)
        bot.send_message(message.chat.id, "TwitchMetr - работает только в группах.", reply_markup=markup)

@bot.message_handler(commands=['stats'])
def stats_message(message):
    if message.chat.type in ['group', 'supergroup']:
        chat_id = message.chat.id

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT user_id, followers FROM streams WHERE chat_id = %s ORDER BY followers DESC LIMIT 10", (str(chat_id),))
        users = cur.fetchall()
        cur.close()
        conn.close()

        if not users:
            bot.send_message(chat_id, "Статистика пуста")
            return
        
        response = "Статистика чата:\n\n"
        for index, user in enumerate(users, start=1):
            try:
                member = bot.get_chat_member(chat_id, int(user['user_id']))
                name = member.user.first_name
            except Exception:
                name = f"{user['user_id']}"

            response += f"{index}. {name}: {user['followers']} фолловеров\n"
        
        bot.send_message(chat_id, response)
    else: 
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("Добавить в группу", url="https://t.me/twitchmetrbot?startgroup")
        markup.add(btn)
        bot.send_message(message.chat.id, "TwitchMetr - работает только в группах.", reply_markup=markup)

bot.polling(none_stop=True)