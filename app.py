import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command, CommandObject
from pybooru import Danbooru, PybooruError
import sqlite3
from loguru import logger
from repo import Repo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from environs import load_dotenv

load_dotenv()

bot_token: str = os.getenv('BOT_TOKEN')
admin_id: int = os.getenv('ADMIN')


if not bot_token:
    logger.error('Не найден токен телеграм бота!')
    exit()

# Объект бота
bot = Bot(token=bot_token, parse_mode='HTML')
# Диспетчер
dp = Dispatcher()
scheduler = AsyncIOScheduler()

danbooru = Danbooru('danbooru')
conn = sqlite3.connect('database/db.sqlite')
repo = Repo(conn)
repo.create_schema()


def get_new_posts_by_tags(tags:str=None) -> list|None:    
    '''
    Принимает тэги и возвращает список постов
    '''
    if tags is None:
        return None

    posts = danbooru.post_list(tags=tags, limit=10)
    posts = repo.filter_new_posts(posts=posts)
    return posts


@dp.message(Command('start'))
async def start(message: types.Message):
    await message.answer("Привет, я booru бот!")
    await asyncio.sleep(.7)
    await message.answer(
        '''<b>Я могу следить за обновления твоих любимых Danbooru тэгов\n
        /add tag Добавить тэг в подписки\n
        /subs Посмотреть подписки\n
        /del tag Удалить подписку</b>
    '''
    )


@dp.message(Command('add'))
async def start(message: types.Message, command: CommandObject):
    if command.args:
        if repo.add_subscription(command.args):
            await message.answer(f'<b>✅ {command.args} - подписка добавлена!</b>')
        else:
            await message.answer(f'<b>❌ Не получилось добавить {command.args} в базу ❌</b>')
    else:
        await message.answer('<b>❌ Нужно указать тэг или тэги для подписки ❌</b>')


@dp.message(Command('subs'))
async def show_subs(message: types.Message, command: CommandObject):
    subs = repo.get_subscriptions_list()
    if subs:
        await message.answer(f'<b>Активных подписок: {len(subs)}</b>')
        await message.answer('\n'.join(subs))
    else:
        await message.answer('<b>Подписки не найдены</b>')


@dp.message(Command('del'))
async def delete_sub(message: types.Message, command: CommandObject):
    if command.args:
        repo.delete_sub(command.args)
        await message.answer(f'✅ <b>{command.args} -  удалено из подписок</b>')


async def check_new_posts(bot:Bot):
    '''
    Получаем список подписок, проверяем обновления для каждого элемента и отправляем новые посты в чат
    '''
    subs = repo.get_subscriptions_list()
    new_posts = []

    if subs:
        for sub in subs:
            posts = get_new_posts_by_tags(sub)
            if posts:
                for post in posts:
                    new_posts.append(post)

    if len(new_posts) > 0:
        for post in new_posts:
            if post:
                _, ext = os.path.splitext(post)
                if ext.lower() in ('.jpg', '.jpeg', '.png'):
                    await bot.send_photo(chat_id=admin_id, photo=post)
                elif ext.lower() in ('.mp4', '.webm'):
                    await bot.send_video(chat_id=admin_id, video=post)
                elif ext.lower() == '.gif':
                    await bot.send_animation(chat_id=admin_id, animation=post)
                await asyncio.sleep(1)
    else:
        await bot.send_message(chat_id=admin_id, text='🤷 <b>Новые сообщения не найдены</b>')


async def main():
    scheduler.add_job(check_new_posts, 'interval', hours=1, args=(bot,))
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())