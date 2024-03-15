# Herzen Schedule Bot
_Телеграм бот, показывающий расписание занятий РГПУ им. Герцена_

## Как запустить

### Debug mode

1. Клонируем репозиторий
    - Linux
    ```sh
    git clone https://github.com/dant4ick/Herzen_Schedule_Bot.git && cd Herzen_Schedule_Bot/
    ```
    - Windows
    ```sh
    ```

2. Создаем виртуальное окружение и активируем
    - Linux
    ```sh
    pyhton3.10 -m venv .venv && source .venv/bin/activate
    ```
    - Windows
    ```sh
    ```

3. Устанавливаем зависимости
    - Linux
    ```sh
    pip install -r requirements.txt
    ```
    - Windows
    ```sh
    ```

4. Создаем файл запуска (важно, так как необходимы **переменные окружения**), для примера смотри [файл](start_example.sh).
    
    4.1 Примечание: чтобы запустить бота в дебаг режиме, необходимо передать в аргументы `--debug`:
    - Linux
    ```sh
    python3 run.py --debug
    ```
    - Windows
    ```sh
    ```

5. Запускаем:
    - Linux
    ```sh
    sh start.sh
    ```
    - Windows
    ```sh
    ```

### Production mode

...