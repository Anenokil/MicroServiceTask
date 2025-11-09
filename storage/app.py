import json
import psycopg
from psycopg.rows import dict_row
from flask import Flask, request, jsonify

app = Flask(__name__)


def get_db_connection():
    conn = psycopg.connect(
        host='db',
        dbname='mydb',
        user='user',
        password='password',
        port=5432
    )
    return conn


def init_db():
    conn = get_db_connection()

    # Таблица для сырых данных
    conn.execute('''
        CREATE TABLE IF NOT EXISTS raw_data (
            id SERIAL PRIMARY KEY,
            features JSONB NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Таблица для обработанных данных
    conn.execute('''
        CREATE TABLE IF NOT EXISTS processed_data (
            id SERIAL PRIMARY KEY,
            features JSONB NOT NULL,
            predictions JSONB NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()


@app.route('/data/raw', methods=['POST'])
def store_raw_data():
    data = request.json.get('data', [])

    conn = get_db_connection()

    try:
        for item in data:
            features_json = json.dumps(item)
            conn.execute(
                'INSERT INTO raw_data (features) VALUES (%s)',
                (features_json,)
            )
        conn.commit()
        return jsonify({'status': 'success', 'count': len(data)})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/data/processed', methods=['POST'])
def store_processed_data():
    data = request.json.get('data', [])

    conn = get_db_connection()

    try:
        for item in data:
            features_json = json.dumps(item.get('features', {}))
            predictions_json = json.dumps(item.get('predictions', {}))

            conn.execute(
                'INSERT INTO processed_data (features, predictions) VALUES (%s, %s)',
                (features_json, predictions_json)
            )
        conn.commit()
        return jsonify({'status': 'success', 'count': len(data)})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/data/raw', methods=['GET'])
def get_raw_data():
    conn = get_db_connection()

    try:
        cursor = conn.cursor(row_factory=dict_row)
        cursor.execute('SELECT * FROM raw_data ORDER BY timestamp DESC LIMIT 100')
        rows = cursor.fetchall()

        data = []
        for row in rows:
            data.append({
                'id': row['id'],
                'features': row['features'],
                'timestamp': row['timestamp'].isoformat()
            })

        return jsonify({'data': data})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/data/clear', methods=['POST'])
def clear_data():
    conn = get_db_connection()

    try:
        conn.execute('DELETE FROM raw_data')
        conn.execute('DELETE FROM processed_data')
        conn.commit()
        return jsonify({'status': 'success', 'message': 'All data cleared'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/health', methods=['GET'])
def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.close()
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'database': 'disconnected', 'error': str(e)}), 500


@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'service': 'Storage',
        'status': 'healthy',
        'endpoints': {
            '/data/raw': 'POST - сохранить сырые данные, GET - получить сырые данные',
            '/data/processed': 'POST - сохранить обработанные данные',
            '/health': 'GET - проверка здоровья'
        }
    })


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
