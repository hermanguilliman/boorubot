from loguru import logger
from sqlite3 import Connection


def init_database(db:Connection):
    # Создается скелет базы данных
    db.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY)')
    db.execute('CREATE TABLE IF NOT EXISTS subscriptions (id INTEGER PRIMARY KEY, tags VARCHAR(255) UNIQUE)')
    db.commit()


def get_all_subscriptions(db:Connection):
    tags = db.execute("SELECT DISTINCT tags FROM subscriptions;").fetchall()
    return tags
    

def add_subscription(db:Connection, tags:str) -> bool:
    # добавить tags в подписки
    try:            
        db.execute("INSERT INTO subscriptions (tags) VALUES (?);", (tags,))
        db.commit()
        return True
    except:
        logger.debug('Ошибка добавления записи')
        return False


def upsert_subscription(db:Connection, id:int, tags:str):
    # обновляем существующую запись по id
    result = db.execute('SELECT * FROM subscriptions WHERE id = ?', (id,)).fetchone()
    
    if result is None:
        # если подписка с данным id не найдена, создаем новую запись
        db.execute('INSERT INTO subscriptions (id, tags) VALUES (?, ?)', (id, tags))
        logger.info('Запись создана')
    else:
        # если подписка с данным id уже существует, обновляем информацию о ней
        db.execute('UPDATE subscriptions SET tags = ? WHERE id = ?', (tags, id))
        logger.info('Запись обновлена')
    db.commit()


def log_posts_to_database(db:Connection, posts:list) -> list:
    # Записывает id постов в базу
    for post in posts:
        if db.execute('SELECT id FROM posts WHERE id = ?', (post['id'],)).fetchone() is None:
            db.execute('INSERT INTO posts (id) VALUES (?)', (post['id'],))
    db.commit()