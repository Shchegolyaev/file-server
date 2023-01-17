# Файловое хранилище
Файловое хранилище, которое позволяет хранить различные типы файлов - документы, фотографии, другие данные.

## Запуск
1. Run Docker-compose
```
docker-compose up --build
  ```
3. Go to docs
```angular2html
http://127.0.0.1:8080/api/openapi
```
## Описание 

**http-сервис**, который обрабатывает поступающие запросы. Сервер стартует по адресу `http://127.0.0.1:8080`.

<details>
<summary> Список  эндпойнтов </summary>

1. Статус активности связанных сервисов

```
GET /ping
```
Получить информацию о времени доступа ко всем связанным сервисам, например, к БД, кэшам, примонтированным дискам, etc.

**Response**
```json
{
    "db": 1.27,
    "cache": 1.89,
    ...
    "service-N": 0.56
}
```

2. Регистрация пользователя.

```
POST /register
```
Регистрация нового пользователя. Запрос принимает на вход логин и пароль для создания новой учетной записи.


3. Авторизация пользователя.

```
POST /auth
```
Запрос принимает на вход логин и пароль учетной записи и возвращает авторизационный токен. Далее все запросы проверяют наличие токена в заголовках - `Authorization: Bearer <token>`


4. Информация о загруженных файлах

```
GET /files/list
```
Вернуть информацию о ранее загруженных файлах. Доступно только авторизованному пользователю.

**Response**
```json
{
    "account_id": "AH4f99T0taONIb-OurWxbNQ6ywGRopQngc",
    "files": [
          {
            "id": "a19ad56c-d8c6-4376-b9bb-ea82f7f5a853",
            "name": "notes.txt",
            "created_ad": "2020-09-11T17:22:05Z",
            "path": "/homework/test-fodler/notes.txt",
            "size": 8512,
            "is_downloadable": true
          },
        ...
          {
            "id": "113c7ab9-2300-41c7-9519-91ecbc527de1",
            "name": "tree-picture.png",
            "created_ad": "2019-06-19T13:05:21Z",
            "path": "/homework/work-folder/environment/tree-picture.png",
            "size": 1945,
            "is_downloadable": true
          }
    ]
}
```


5. Загрузить файл в хранилище

```
POST /files/upload
```
Метод загрузки файла в хранилище. Доступно только авторизованному пользователю.
Для загрузки заполняется полный путь до файла, в который будет загружен/переписан загружаемый файл. Если нужные директории не существуют, то они будут созданы автоматически.
Так же, есть возможность указать путь до директории. В этом случае имя создаваемого файла будет создано в соответствии с текущим передаваемым именем файла.

**Request parameters**
```
{
    "path": <full-path-to-save-file>||<path-to-folder>,
}
```
**Response**
```json
{
    "id": "a19ad56c-d8c6-4376-b9bb-ea82f7f5a853",
    "name": "notes.txt",
    "created_ad": "2020-09-11T17:22:05Z",
    "path": "/homework/test-fodler/notes.txt",
    "size": 8512,
    "is_downloadable": true
}
```


6. Скачать загруженный файл

```
GET /files/download
```
Скачивание ранее загруженного файла. Доступно только авторизованному пользователю.

**Path parameters**
```
/?path=<path-to-file>||<file-meta-id>
```
Возможность скачивания есть как по переданному пути до файла, так и по идентификатору.


</details>


## Дополнительные возможности:

- Добавление возможности скачивания в архиве
