import telebot
import psycopg2
from psycopg2 import sql

DB_CONFIG = {
    "database": "NEFTG",
    "user": "postgres",
    "password": "q20081004",
    "host": "localhost",
    "port": "5432",
}

bot = telebot.TeleBot('8574045363:AAEbZR8euBvfwthO8HfEt45Aq2cilhLk3xw')

def connection ():
    return psycopg2.connect(**DB_CONFIG)

def init_db():
    conn = connection()
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        post_id BIGINT PRIMARY KEY,
        chanel_id BIGINT,
        post_text TEXT,
        post_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS reactions (
        id SERIAL PRIMARY KEY,
        post_id BIGINT REFERENCES posts(post_id) ON DELETE CASCADE,
        emoji VARCHAR(50), 
        counter INTEGER
    );
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS post_media (
    id SERIAL PRIMARY KEY,
    post_id BIGINT REFERENCES posts(post_id) ON DELETE CASCADE,
    file_id VARCHAR(255),
    media_type VARCHAR(20)
    );
    ''')

    conn.commit()
    cur.close()
    conn.close()
    print("бд готова")

init_db()

@bot.channel_post_handler(content_types=['photo', 'video', 'text'])
def handle_post(message):
    post_id = message.message_id
    chanel_id = message.chat.id
    text = message.caption or message.text or ""

    conn = connection()
    cur = conn.cursor()

    cur.execute('''
        INSERT INTO posts (post_id, chanel_id, post_text)
        VALUES (%s, %s, %s)
        ON CONFLICT (post_id) DO NOTHING
    ''', (post_id, chanel_id, text))

    conn.commit()
    conn.close()
    cur.close()

    if message.content_type == "photo":
        file_id = message.photo[-1].file_id
        save_media(post_id, file_id, "photo")
    elif message.content_type == "video":
        file_id = message.video.file_id
        save_media(post_id, file_id, "video")

def save_media (post_id, file_id, m_type):
    conn = connection()
    cur = conn.cursor()

    cur.execute('''
    INSERT INTO post_media (post_id, file_id, media_type)
    VALUES (%s, %s, %s);
    ''', (post_id, file_id, m_type))

    conn.commit()
    cur.close()
    conn.close()

@bot.message_reaction_count_handler()
def reaction_change(update):
    conn = connection()
    cur = conn.cursor()

    post_id = update.message_id
    reaction_list = update.reactions

    try:
        cur.execute('DELETE FROM reactions WHERE post_id = %s', (post_id,))

        for react in reaction_list:
            emoji = react.type.emoji if react.type.type == "emoji" else 'custom'
            count = react.total_count

            cur.execute('''
                INSERT INTO reactions (post_id, emoji, counter)
                VALUES (%s, %s, %s)
            ''', (post_id, emoji, count))
        conn.commit()
    
    except Exception as e:
        print(f"ошибка при обновлении реакций {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    try:
        init_db()

        print("🚀 Бот вышел на связь...")
        bot.infinity_polling(allowed_updates=['message', 'channel_post', 'message_reaction_count'])

    except Exception as e:
        print(f"❌ Критическая ошибка при запуске: {e}")