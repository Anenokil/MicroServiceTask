from flask import Flask, jsonify, request
import pandas as pd
import logging
import os
from datetime import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataCollector:
    def __init__(self):
        self.download_log = []
        self.data_path = 'data/sample_data.csv'

    def get_batch(self, batch_size=10):
        try:
            if not os.path.exists(self.data_path):
                logger.error(f'Data file not found: {self.data_path}')
                return self._generate_test_data(batch_size)

            df = pd.read_csv(self.data_path)
            batch = df.head(batch_size).to_dict('records')

            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'batch_size': len(batch),
                'status': 'success'
            }
            self.download_log.append(log_entry)

            return batch
        except Exception as e:
            logger.error(f'Error collecting data: {e}')
            return self._generate_test_data(batch_size)

    def _generate_test_data(self, batch_size):
        test_data = []
        for i in range(batch_size):
            test_data.append({
                'feature1': float(i) + 0.1,
                'feature2': float(i) + 1.1,
                'feature3': float(i) + 2.1,
                'feature4': float(i) + 3.1,
                'target': i % 2
            })

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'batch_size': len(test_data),
            'status': 'test_data_generated'
        }
        self.download_log.append(log_entry)

        return test_data


collector = DataCollector()


@app.route('/batch', methods=['GET'])
def get_batch():
    batch_size = request.args.get('batch_size', 10, type=int)
    data = collector.get_batch(batch_size)
    return jsonify({'data': data, 'count': len(data)})


@app.route('/logs', methods=['GET'])
def get_logs():
    return jsonify({'logs': collector.download_log})


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
            '/health': 'GET - проверка здоровья'
        }
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
