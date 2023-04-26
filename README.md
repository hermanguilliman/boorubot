# Бот для отслеживания обновлений по тэгам Danbooru

Клонируйте репозиторий

```bash
git clone git@github.com:hermanguilliman/boorubot.git
```

Соберите образ

```bash
docker build -t boorubot .
```

Запустите контейнер

```bash
docker run -d --restart always -e ADMIN=123456 -e BOT=123456 boorubot
