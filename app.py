import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command, CommandObject
from pybooru import Danbooru
import sqlite3
from repo import Repo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from environs import load_dotenv

load_dotenv()


bot_token: str = os.getenv('BOT')
admin_id: int = int(os.getenv('ADMIN'))


if not bot_token:
    logger.error('Не найден токен телеграм бота!')
    exit()

bot = Bot(token=bot_token, parse_mode='HTML')
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

    last_posts = danbooru.post_list(tags=tags, limit=10)
    new_posts = repo.filter_new_posts(posts=last_posts)
    return new_posts


@dp.message(Command('start'))
async def start(message: types.Message):
    if message.from_user.id != admin_id:
        return
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
    if message.from_user.id != admin_id:
        return
    if command.args:
        if repo.add_subscription(command.args):
            await message.answer(f'<b>✅ {command.args} - подписка добавлена!</b>')
            await check_new_posts(bot=bot)
        else:
            await message.answer(f'<b>❌ Не получилось добавить {command.args} в базу ❌</b>')
    else:
        await message.answer('<b>❌ Нужно указать тэг или тэги для подписки ❌</b>')


@dp.message(Command('subs'))
async def show_subs(message: types.Message):
    if message.from_user.id != admin_id:
        return
    subs = repo.get_subscriptions_list()
    if len(subs) > 0:
        await message.answer(f'<b>Активных подписок: {len(subs)}</b>')
        await asyncio.sleep(1)
        await message.answer(', '.join(subs))
    else:
        await message.answer('<b>Подписки не найдены</b>')


@dp.message(Command('del'))
async def delete_sub(message: types.Message, command: CommandObject):
    if message.from_user.id != admin_id:
        return
    if command.args:
        await message.answer(f'Удаляю {command.args}...')
        await asyncio.sleep(1)
        if repo.delete_sub(command.args):
            await message.answer(f'✅ <b>{command.args} -  удалено из подписок</b>')
        else:
            await message.answer(f'<b>❌ Не получилось удалить {command.args}</b>')
    else:
        await message.answer('Используйте <b>/del tag</b> чтобы удалить подписку')


async def check_new_posts(bot:Bot):
    '''
    Получаем список подписок, проверяем обновления для каждого элемента и отправляем новые посты в чат
    '''
    logger.info('Проверка новых сообщений')
    subs = repo.get_subscriptions_list()
    new_posts = []

    if subs:
        # Получаем новые посты по каждому набору тэгов
        for sub in subs:
            posts = get_new_posts_by_tags(sub)
            if posts:
                    for post in posts:
                        new_posts.append(post)

    if len(new_posts) > 0:
        # Если есть список новых постов

        for post in new_posts:
            if 'file_url' in post:
                caption = f"<b>artist:</b> {post['tag_string_artist']}\n<b>tags:</b> {post['tag_string_general']}" 
                if post['file_ext'] in ('jpg', 'jpeg', 'png', 'webp'):
                    await bot.send_photo(chat_id=admin_id, photo=post['file_url'], caption=caption, parse_mode='HTML')
                elif post['file_ext'] in ('mp4', 'webm'):
                    await bot.send_video(chat_id=admin_id, video=post['file_url'], caption=caption, parse_mode='HTML')
                elif post['file_ext'] == 'gif':
                    await bot.send_animation(chat_id=admin_id, animation=post['file_url'], caption=caption, parse_mode='HTML')
                else:
                    logger.debug(f"Не знаю что делать с форматом {post['file_ext']}")
                await asyncio.sleep(1)
    else:
        logger.info('Новые сообщения не найдены')


async def main():
    scheduler.add_job(check_new_posts, 'interval', hours=1, args=(bot,))
    scheduler.start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())