import os
import time
from threading import Timer
from functools import lru_cache
from flask import Flask, render_template
import psycopg2
from psycopg2.extras import RealDictCursor
import requests

# Узнаем путь к папке, где лежит сам app.py (это папка back)
base_dir = os.path.dirname(os.path.abspath(__file__))
# Указываем, что шаблоны и статика на один уровень выше
root_dir = os.path.join(base_dir, '..')

app = Flask(__name__, 
            template_folder=root_dir, 
            static_folder=os.path.join(root_dir, 'styles'),
            static_url_path='/styles')

DB_CONFIG = {
    "database": "NEFTG",
    "user": "postgres",
    "password": "q20081004",
    "host": "localhost",
    "port": "5432",
}

def connection():
    return psycopg2.connect(**DB_CONFIG)

BOT_TOKEN = '8574045363:AAEbZR8euBvfwthO8HfEt45Aq2cilhLk3xw'

@lru_cache(maxsize=128)
def get_tg_file_url(file_id):
    if not file_id:
        return None
    try:
        # 1. Спрашиваем у Телеге путь к файлу
        response = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}", timeout=5)
        data = response.json()
        if data.get('ok'):
            file_path = data['result']['file_path']
            # 2. Формируем прямую ссылку (она живет около часа)
            return f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    except Exception as e:
        print(f"Ошибка получения ссылки: {e}")
    return None

def get_posts():
    conn = connection()
    # RealDictCursor превращает строки БД в удобные словари Python
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Этот запрос собирает пост и "приклеивает" к нему массивы медиа и реакций
    query = """
    SELECT 
        p.post_id, 
        p.post_text, 
        p.post_date,
        (SELECT json_agg(json_build_object('emoji', r.emoji, 'counter', r.counter)) 
         FROM reactions r WHERE r.post_id = p.post_id) as reactions,
        (SELECT json_agg(json_build_object('file_id', m.file_id, 'media_type', m.media_type)) 
         FROM post_media m WHERE m.post_id = p.post_id) as media
    FROM posts p
    ORDER BY p.post_date DESC;
    """
    
    cur.execute(query)
    posts = cur.fetchall()
    cur.close()
    conn.close()
    return posts

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/activity')
def activity():
    raw_posts = get_posts() 
    # "Прогреваем" ссылки для медиа
    for post in raw_posts:
        if post['media']:
            for item in post['media']:
                # Получаем ссылку через твою функцию с кэшем
                item['url'] = get_tg_file_url(item['file_id'])
                
    return render_template('activity.html', posts=raw_posts)

@app.route("/Merch")
def Merch():
    return render_template('Merch.html')

@app.route("/paschalko")
def paschalko():
    return render_template("paschalko.html")

def clear_cache():
    get_tg_file_url.cache_clear()
    print("Кэш ссылок Telegram очищен!")
    # Запускаем таймер снова на 50 минут (3000 секунд)
    Timer(3000, clear_cache).start()

cache_started = False

@app.before_request
def start_timer():
    global cache_started
    if not cache_started:
        clear_cache()
        cache_started = True

if __name__ == '__main__':
    app.run(debug=True)

