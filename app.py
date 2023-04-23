from pybooru import Danbooru, PybooruError
import sqlite3
from loguru import logger
from database import (
    init_database,
    upsert_subscription,
    log_posts_to_database,
    add_subscription,
    get_all_subscriptions
    )

danbooru = Danbooru('danbooru')
db = sqlite3.connect('db.sqlite')

init_database(db)
# default subs
add_subscription(db=db, tags='ishikei')
add_subscription(db=db, tags="ishikoro_1450")
add_subscription(db=db, tags="porqueloin")
get_all_subscriptions(db)

def get_posts_list() -> list|None:    
    try:
        posts = danbooru.post_list(tags='ishikei', limit=10)
        posts = danbooru.list(tags='ishikei', limit=10)
        posts = get_posts_list()
        if posts:
            log_posts_to_database(db=db, posts=posts)
        print('Получено ', len(posts), ' постов')
        return posts
    except:
        logger.error('Ошибка!')

