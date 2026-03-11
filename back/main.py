import os
import telebot
import psycopg2
from psycopg2 import sql

from dotenv import load_dotenv

ADMIN_ID = [1306570088, 1341021324]

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)
db_pass = os.getenv("DB_PASSWORD")
bot_token = os.getenv("BOT_TOKEN")

DB_CONFIG = {
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": db_pass,
    "host": "localhost",
    "port": "5432",
}

bot = telebot.TeleBot(bot_token)

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
        post_id INTEGER REFERENCES posts(post_id),
        file_id TEXT,
        media_type TEXT,
        media_group_id TEXT  -- ОБЯЗАТЕЛЬНО ДОБАВЬ ЭТО
    );
    ''')

    conn.commit()
    cur.close()
    conn.close()
    print("бд готова")

init_db()

# @bot.channel_post_handler(content_types=['photo', 'video', 'text'])
# def handle_post(message):
#     post_id = message.message_id
#     channel_id = message.chat.id
#     m_group_id = message.media_group_id  # Тот самый ключ к альбомам
#     text = message.caption or message.text or ""

#     conn = connection()
#     cur = conn.cursor()

#     try:
#         target_post_id = post_id

#         # ЛОГИКА СКЛЕЙКИ АЛЬБОМА
#         if m_group_id:
#             # Проверяем, не залетало ли уже что-то из этого альбома
#             cur.execute('SELECT post_id FROM post_media WHERE media_group_id = %s LIMIT 1', (m_group_id,))
#             result = cur.fetchone()
#             if result:
#                 target_post_id = result[0]

#         # 1. Работаем с основным постом
#         # Используем UPDATE, чтобы если текст пришел не в первом сообщении, он все равно сохранился
#         cur.execute('''
#             INSERT INTO posts (post_id, chanel_id, post_text)
#             VALUES (%s, %s, %s)
#             ON CONFLICT (post_id) DO UPDATE SET 
#             post_text = CASE WHEN EXCLUDED.post_text <> '' THEN EXCLUDED.post_text ELSE posts.post_text END
#         ''', (target_post_id, channel_id, text))

#         # 2. Определяем медиа
#         file_id = None
#         m_type = None
#         if message.content_type == "photo":
#             file_id = message.photo[-1].file_id
#             m_type = "photo"
#         elif message.content_type == "video":
#             file_id = message.video.file_id
#             m_type = "video"

#         # 3. Сохраняем медиа (если оно есть)
#         if file_id:
#             cur.execute('''
#                 INSERT INTO post_media (post_id, file_id, media_type, media_group_id)
#                 VALUES (%s, %s, %s, %s)
#                 ON CONFLICT DO NOTHING
#             ''', (target_post_id, file_id, m_type, m_group_id))

#         conn.commit()
#         print(f"✅ Пост {target_post_id} обработан (Media: {m_type})")

#     except Exception as e:
#         print(f"❌ Ошибка в handle_post: {e}")
#         conn.rollback()
#     finally:
#         cur.close()
#         conn.close()

# @bot.message_reaction_count_handler()
# def reaction_change(update):
#     conn = connection()
#     cur = conn.cursor()

#     post_id = update.message_id
#     reaction_list = update.reactions

#     try:
#         # ПРОВЕРКА: есть ли вообще такой пост в нашей таблице posts?
#         cur.execute('SELECT 1 FROM posts WHERE post_id = %s', (post_id,))
#         post_exists = cur.fetchone()

#         if not post_exists:
#             # Если поста нет, мы не можем добавить реакцию из-за Foreign Key.
#             # Просто выходим, чтобы не было ошибки в консоли.
#             return

#         # Если пост найден, обновляем реакции как обычно
#         cur.execute('DELETE FROM reactions WHERE post_id = %s', (post_id,))

#         for react in reaction_list:
#             emoji = react.type.emoji if react.type.type == "emoji" else 'custom'
#             count = react.total_count

#             cur.execute('''
#                 INSERT INTO reactions (post_id, emoji, counter)
#                 VALUES (%s, %s, %s)
#             ''', (post_id, emoji, count))
            
#         conn.commit()
    
#     except Exception as e:
#         # Теперь сюда будут падать только реальные ошибки (например, обрыв связи с БД)
#         print(f"Ошибка при обновлении реакций: {e}")
#         conn.rollback()
#     finally:
#         cur.close()
#         conn.close()


# Словарь для хранения связки: {media_group_id: original_post_id}
album_storage = {}

@bot.message_handler(
    func=lambda message: message.forward_from_chat is not None, 
    content_types=['text', 'photo', 'video']
)
def handle_imported_post(message):
    if message.from_user.id in ADMIN_ID:
        old_post_id = message.forward_from_message_id
        m_group_id = message.media_group_id
        post_text = message.text or message.caption or ""
        
        # Решаем, под каким ID сохранять медиа
        # Если это альбом, и мы уже сохранили его первое сообщение
        if m_group_id and m_group_id in album_storage:
            target_post_id = album_storage[m_group_id]
        else:
            # Если это не альбом или первое сообщение альбома
            target_post_id = old_post_id
            if m_group_id:
                album_storage[m_group_id] = old_post_id

        conn = connection()
        cur = conn.cursor()
        try:
            # 1. Создаем или обновляем основной пост (текст берем только если он есть)
            if post_text or not m_group_id or (m_group_id not in album_storage):
                cur.execute('''
                    INSERT INTO posts (post_id, chanel_id, post_text)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (post_id) DO UPDATE SET 
                    post_text = CASE WHEN EXCLUDED.post_text <> '' THEN EXCLUDED.post_text ELSE posts.post_text END
                ''', (target_post_id, message.forward_from_chat.id, post_text))
            
            # 2. Сохраняем медиа, привязывая его к target_post_id
            file_id = None
            media_type = None

            if message.photo:
                file_id = message.photo[-1].file_id
                media_type = 'photo'
            elif message.video:
                file_id = message.video.file_id
                media_type = 'video'
            
            if file_id:
                cur.execute('''
                    INSERT INTO post_media (post_id, file_id, media_type)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                ''', (target_post_id, file_id, media_type))

            conn.commit()
            print(f"✅ Обработано: {media_type if file_id else 'text'} для поста {target_post_id}")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            conn.rollback()
        finally:
            cur.close()
            conn.close()

@bot.message_handler(commands=['clear'])
def clear_database(message):
    if message.from_user.id in ADMIN_ID:
        conn = connection()
        cur = conn.cursor()
        try:
            cur.execute('TRUNCATE posts, post_media, reactions RESTART IDENTITY CASCADE;')
            conn.commit()
            bot.reply_to(message, "🗑 База полностью очищена!")
        except Exception as e:
            bot.reply_to(message, f"ошибка очистки: {e}")
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