# Проект LoginInfo

Этот проект содержит скрипт Python, который собирает информацию о системе и пользователях, а затем записывает эти данные в базу данных MySQL.

## Начало работы

Эти инструкции помогут вам подготовить проект для запуска на вашем локальном компьютере для разработки и тестирования. Смотрите раздел "Развертывание" для описания того, как развернуть проект в системе.

### Предварительные условия

Для запуска этого скрипта вам потребуется следующее окружение:

- Python 3.6 или выше
- Библиотеки Python: `mysql.connector`, `os`, `json`, `platform`, `subprocess`, `datetime`, `shutil`, `glob`
- MySQL сервер

### Установка

Клонируйте репозиторий с помощью Git:

```bash
git clone https://github.com/Ceasy/logininfo.git
```

Клонируйте репозиторий с помощью Git:
```bash 
cd getUsersInfo
```
Установите необходимые зависимости:
```bash
pip install -r requirements.txt
```

### Настройка

Перед запуском скрипта настройте переменные среды для подключения к базе данных:

```bash
setx DB_HOST "IP_SERVER" /M
```
```bash
setx DB_DATABASE "DB_NAME" /M
```
```bash
setx DB_USER "USER_DB" /M
```
```bash
setx DB_PASSWORD "PASS_USER" /M
```
### Запуск

Запустите скрипт:
```bash
python script.py
```
### Развертывание

Для развертывания скрипта в домене Windows используйте Групповые Политики для создания запланированного задания, которое
будет запускать скрипт на целевых компьютерах.

### Авторы

    Алексей Федотов - Ceasy

### Лицензия

Этот проект распространяется под лицензией MIT. Смотрите файл LICENSE.md для дополнительной информации.

### Благодарности
Спасибо всем, кто вносил вклад в разработку и поддержку этого проекта.