# Micro Service Task

## Сервисы:

- Web Master - единая точка входа, маршрутизация запросов
- Collector - сбор и выдача батчей данных
- Storage - хранение данных в PostgreSQL
- ML Service - обучение моделей и предсказания

## Основные API endpoints

- ```GET  /system/health                    # Проверка состояния системы```
- ```GET  /api/collector/batch?size=N       # Получить данные```
- ```POST /api/storage/data/raw             # Сохранить данные```
- ```POST /api/storage/data/clear           # Очистить БД```
- ```POST /api/ml/train                     # Обучить модель```
- ```POST /api/ml/predict                   # Предсказание```
- ```GET  /api/ml/model/info                # Информация о модели```

## Рабочий процесс

Запуск системы:
```bash
sudo docker compose up --build
```

Проверка здоровья:
```bash
curl http://localhost:5000/system/health
```

Сбор данных:
```bash
curl "http://localhost:5000/api/collector/batch?batch_size=20"
```

Сохранение в БД:
```bash
curl -X POST http://localhost:5000/api/storage/data/raw \
  -H "Content-Type: application/json" \
  -d '{"data": [{"feature1": 1.0, "feature2": 2.0, "feature3": 3.0, "feature4": 4.0, "target": 1}]}'
```

Обучение модели:
```bash
curl -X POST http://localhost:5000/api/ml/train
```

Предсказание:
```bash
curl -X POST http://localhost:5000/api/ml/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [1.0, 2.0, 3.0, 4.0]}'
```

## Структура проекта

```text
project/
├─ collector/     # Сбор данных
├─ storage/       # Хранилище (PostgreSQL)
├─ ml_service/    # ML модели
├─ web_master/    # API
└─ docker-compose.yml
```
