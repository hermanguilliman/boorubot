from loguru import logger
from sqlite3 import Connection

class Repo:
    
    def __init__(self, db: Connection):
        self.db = db
    
    def create_schema(self):
        with open('database/init.sql') as f:
            script = f.read()
            self.db.executescript(script)
            
            
    def get_subscriptions_list(self)-> list:
        # Получение всех подписок
        tags = self.db.execute("SELECT DISTINCT tags FROM subscriptions;").fetchall()
        tags = ["".join(tag) for tag in tags]
        return tags
        

    def add_subscription(self, tags:str) -> bool:
        # добавить tags в подписки
        try:            
            self.db.execute("INSERT INTO subscriptions (tags) VALUES (?);", (tags,))
            self.db.commit()
            return True
        except:
            logger.debug('Ошибка добавления записи')
            return False


    def upsert_subscription(self, id:int, tags:str):
        # обновляем существующую запись по id
        result = self.db.execute('SELECT * FROM subscriptions WHERE id = ?', (id,)).fetchone()
        
        if result is None:
            # если подписка с данным id не найдена, создаем новую запись
            self.db.execute('INSERT INTO subscriptions (id, tags) VALUES (?, ?)', (id, tags))
            logger.info('Запись создана')
        else:
            # если подписка с данным id уже существует, обновляем информацию о ней
            self.db.execute('UPDATE subscriptions SET tags = ? WHERE id = ?', (tags, id))
            logger.info('Запись обновлена')
        self.db.commit()


    def filter_new_posts(self, posts) -> list|None:
        # Фильтрует посты, записывая их в бд и возвращает список ссылок на новые
        if posts:
            new_posts = []
            for post in posts:
                if self.db.execute('SELECT id FROM posts WHERE id = ?', (post['id'],)).fetchone() is None:
                    new_posts.append(post.get('file_url'))
                    self.db.execute('INSERT INTO posts (id) VALUES (?)', (post['id'],))
                self.db.commit()
            return new_posts
        else:
            return None

    def delete_sub(self, tags:str) -> bool:
        # Удаляет запись
        self.db.execute("DELETE FROM subscriptions WHERE tags = ?;", [tags])
        logger.info
        self.db.commit()
