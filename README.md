# Бот для отслеживания обновлений по тэгам Danbooru

[![Интерфейс boorubot](https://i.ibb.co/XCcWPL8/main.png 'Boorubot')](https://i.ibb.co/XCcWPL8/main.png)

Клонируйте репозиторий

```bash
git clone https://github.com/hermanguilliman/boorubot.git
```

Переименуйте .env.example в .env и заполните поля ADMIN id админа и BOT токеном бота

Соберите образ с помощью docker-compose

```bash
docker-compose build
```

Запустите

```bash
docker-compose up -d
```
