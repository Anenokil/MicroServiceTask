import os
from datetime import datetime
import pandas as pd
from flask import Flask, jsonify, request

app = Flask(__name__)


class DataCollector:
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.logs = []

    def get_batch(self, batch_size: int = 10) -> list[dict]:
        if not os.path.exists(self.data_path):
            batch = []
            status = 'error'
            error_msg = 'File not found'
        else:
            try:
                df = pd.read_csv(self.data_path)
                batch = df.head(batch_size).to_dict('records')
            except Exception as e:
                batch = []
                status = 'error'
                error_msg = str(e)
            else:
                status = 'ok'

        # Логгируем
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'requested_batch_size': batch_size,
            'actual_batch_size': len(batch),
            'status': status,
        }
        if status == 'error':
            log_entry['error_msg'] = error_msg
        self.logs.append(log_entry)

        return batch


collector = DataCollector('data/sample_data.csv')


@app.route('/batch', methods=['GET'])
def get_batch():
    batch_size = request.args.get('batch_size', 10, int)
    data = collector.get_batch(batch_size)
    return jsonify({'data': data, 'size': len(data)})


@app.route('/logs', methods=['GET'])
def get_logs():
    return jsonify({'logs': collector.logs})


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})


@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'service': 'Collector',
        'status': 'healthy',
        'endpoints': {
            '/batch': 'GET - получить батч данных',
            '/logs': 'GET - получить логи загрузок',
            '/health': 'GET - проверка здоровья',
        }
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
