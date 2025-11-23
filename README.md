# Test Task Backend

## Запуск проекта

### Шаг 1: Запуск всех сервисов

**Mac/Linux:**
```bash
cd test-task-backend
docker-compose up -d
```

**Windows PowerShell:**
```powershell
cd test-task-backend
docker-compose up -d
```

### Шаг 2: Проверка статуса сервисов

**Mac/Linux:**
```bash
docker-compose ps
```

**Windows PowerShell:**
```powershell
docker-compose ps
```

Все сервисы должны быть в статусе `Up` и `healthy`.

## Тестирование

### Шаг 1: Проверка здоровья API

**Mac/Linux:**
```bash
curl http://localhost:8000/health
```

**Windows PowerShell:**
```powershell
Invoke-RestMethod -Uri http://localhost:8000/health
```

Ожидаемый ответ: `{"status":"healthy","service":"api"}`

### Шаг 2: Проверка корневого эндпоинта

**Mac/Linux:**
```bash
curl http://localhost:8000/
```

**Windows PowerShell:**
```powershell
Invoke-RestMethod -Uri http://localhost:8000/
```

### Шаг 3: Отправка задачи на парсинг

**Mac/Linux:**
```bash
curl -X POST http://localhost:8000/browse \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.avito.ru/moskva/kvartiry/2-k_kvartira_85_m_89_et._1234567890"}'
```

**Windows PowerShell:**
```powershell
Invoke-RestMethod -Uri http://localhost:8000/browse -Method POST -ContentType "application/json" -Body '{"url": "https://www.avito.ru/moskva/kvartiry/2-k_kvartira_85_m_89_et._1234567890"}'
```

Ожидаемый ответ: `{"message":"Задача успешно добавлена в очередь","url":"..."}`

### Шаг 4: Проверка обработки задачи

Проверьте логи consumer для просмотра HTML содержимого:

**Mac/Linux:**
```bash
docker-compose logs -f consumer
```

**Windows PowerShell:**
```powershell
docker-compose logs -f consumer
```

В логах будет полный HTML код страницы, полученный через Selenium.

### Шаг 5: Тестирование с несколькими URL

**Mac/Linux:**
```bash
curl -X POST http://localhost:8000/browse \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.avito.ru/moskva/kvartiry/..."}'

curl -X POST http://localhost:8000/browse \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.avito.ru/spb/kvartiry/..."}'
```

**Windows PowerShell:**
```powershell
Invoke-RestMethod -Uri http://localhost:8000/browse -Method POST -ContentType "application/json" -Body '{"url": "https://www.avito.ru/moskva/kvartiry/..."}'

Invoke-RestMethod -Uri http://localhost:8000/browse -Method POST -ContentType "application/json" -Body '{"url": "https://www.avito.ru/spb/kvartiry/..."}'
```

### Шаг 6: Тестирование валидации URL

**Mac/Linux:**
```bash
curl -X POST http://localhost:8000/browse \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.google.com"}'
```

**Windows PowerShell:**
```powershell
Invoke-RestMethod -Uri http://localhost:8000/browse -Method POST -ContentType "application/json" -Body '{"url": "https://www.google.com"}'
```

Ожидаемый ответ: `{"detail":"URL должен быть с сайта avito.ru"}`

## Остановка проекта

**Mac/Linux:**
```bash
docker-compose down
```

**Windows PowerShell:**
```powershell
docker-compose down
```
