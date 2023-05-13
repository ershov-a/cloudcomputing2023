Файлы для разворачивания бота в Yandex.Cloud.
- `app.py`, `requirements.txt` - для создания функции в `Cloud Functions`. Нужно определить переменные окружения (`GPT_TOKEN`, `TELEGRAM_TOKEN`, `FEEDBACK_GROUP_ID`, `OWM_TOKEN`, `YDB_DATABASE`, `YDB_ENDPOINT`).
- `info-service-bot-gateway` - для создания `API Gateway`. Нужно заменить `URL` и `FUNCTION_ID` на актуальные.
- `init.yql` - файл для создания и инициализации БД для бота. Предварительно нужно создать БД `Managed Service for YDB`.