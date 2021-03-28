# Candy Delivery App
REST API сервис, который позволяет нанимать курьеров на работу, принимает заказы и оптимально распределяет заказы
между курьерами, попутно считая их рейтинг и заработок.


## Зависимости
- `python 3.8`
- всё из `requirements.txt`


## Запуск вручную без Docker
- создать `.env` файл в корне (пример в `.env.example`)
- установить PostgreSQL в качестве сервера БД
- создать базу и указать ее имя в переменной окружения `DB_NAME`
- установать зависимости, накатить миграции и запустить сервер
```bash
$ pip install -r requirements.txt
$ python manage.py migrate
$ python manage.py runserver 0.0.0.0:8080 --noreload
```


## Тестирование (без использования Docker)
При добавлении миграций, базу нужно пересоздавать
### Запуск с созданием базы
```bash
$ pytest --create-db
```


## Запуск c использованием Docker
- установить docker и docker-compose
- билд, запуск docker-контейнеров и накатывание миграций
```bash
$ docker-compose up -d --build
$ docker-compose exec candy_delivery python manage.py migrate --noinput
```
- после успешного запуска docker-контейнеров, приложение будет доступно по адресу: http://0.0.0.0:8080


## Тестирование (c использования Docker)
### Запуск с созданием базы
```bash
$ docker-compose exec candy_delivery pytest --create-db
```
