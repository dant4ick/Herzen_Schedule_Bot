# Herzen Schedule Bot
_Телеграм бот, показывающий расписание занятий РГПУ им. Герцена_

## Как запустить

### Debug mode

1. Клонируем репозиторий
    ```sh
    git clone https://github.com/dant4ick/Herzen_Schedule_Bot.git && cd Herzen_Schedule_Bot/
    ```

2. Создаем виртуальное окружение и активируем
    - Linux
        ```sh
        pyhton3.10 -m venv .venv && source .venv/bin/activate
        ```
    - Windows
    
        Если не установлена версия `python==3.10`, устанавливаем с [официального сайта](https://www.python.org/downloads/).

        _ВАЖНО: Если у вас установлена более свежая версия, убедитесь, что опция __Add Python 3.10 to PATH__ НЕ АКТИВНА_

        ```batch
        py -3.10 -m venv .venv && .venv\Scripts\activate.bat
        ```

3. Устанавливаем зависимости
    ```sh
    pip install -r requirements.txt
    ```

4. Создаем файл запуска (важно, так как необходимы __переменные окружения__), для примера смотри [файл](start_example.sh).
    
    4.1 Примечание: чтобы запустить бота в дебаг режиме, необходимо передать в аргументы `--debug`:
    - Linux
        ```sh
        python3 run.py --debug
        ```
    - Windows
        ```batch
        @echo off

        set TELEGRAM_TOKEN="123"
        set ADMIN_TELEGRAM_ID="123"

        set WEBHOOK_HOST=https://example.com
        set WEBAPP_PORT=5000

        set DONATE_URL=https://pay.cloudtips.ru/p/0a19cb8e
        set SUBSCRIBE_URL=https://boosty.to/dant4ick

        :loop
        python run.py --debug
        if errorlevel 1 (
            echo The program crashed at %time%. Restarting the script...
            goto loop
        )
        ```

5. Запускаем:
    - Linux
        ```sh
        sh start.sh
        ```
    - Windows
        ```batch
        start.bat
        ```

### Production mode

...