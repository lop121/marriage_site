# Django Marriage Site

## Быстрый старт для запуска проекта через Docker

### 1. Клонируй репозиторий

```bash
git clone https://github.com/lop121/marriage_site
cd marriage_site
```

2. Создай файл .env на основе .env.example

```
cp .env.example .env
```

Проверь значения переменных, при необходимости измени их (например, SECRET_KEY, DB_NAME и т.д.).

3. Установи [Docker и Docker Compose](https://www.docker.com/products/docker-desktop/)

4. Собери и запусти контейнеры

```bash
docker compose up --build
```

5. Выполни миграции

```bash
docker compose exec web python manage.py migrate
```

6. Загрузить тестовые данные

```
docker compose exec web python manage.py loaddata db.json
```

7. (По желанию) Создай суперпользователя

```
docker compose exec web python manage.py createsuperuser
```

8. Открой сайт и перейди в браузере по адресу: http://localhost/