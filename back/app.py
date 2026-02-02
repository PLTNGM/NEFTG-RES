import os
from flask import Flask, render_template
import psycopg2
from psycopg2.extras import RealDictCursor
import requests

app = Flask(__name__, template_folder='../',
            static_folder='../styles',
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

@app.route('/')
def index():
    all_posts = get_posts()
    # Мы передаем переменную all_posts в HTML под именем 'posts'
    return render_template('activity.html', posts=all_posts, get_url=get_tg_file_url)

if __name__ == '__main__':
    app.run(debug=True)

