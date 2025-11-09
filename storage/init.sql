-- Создание таблицы для сырых данных
CREATE TABLE IF NOT EXISTS raw_data (
    id SERIAL PRIMARY KEY,
    features JSONB NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание таблицы для обработанных данных
CREATE TABLE IF NOT EXISTS processed_data (
    id SERIAL PRIMARY KEY,
    features JSONB NOT NULL,
    predictions JSONB NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создание индексов для ускорения запросов
CREATE INDEX IF NOT EXISTS idx_raw_data_timestamp ON raw_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_processed_data_timestamp ON processed_data(timestamp);
