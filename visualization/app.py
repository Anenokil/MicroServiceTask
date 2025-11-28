import os
import requests
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

WEB_MASTER_URL = os.getenv('WEB_MASTER_URL', 'http://web_master:5000')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/system/health')
def system_health():
    try:
        response = requests.get(f'{WEB_MASTER_URL}/system/health', timeout=5)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/collector/batch', methods=['GET'])
def get_batch():
    try:
        batch_size = request.args.get('batch_size', 10)
        response = requests.get(
            f'{WEB_MASTER_URL}/api/collector/batch',
            params={'batch_size': batch_size},
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/storage/data', methods=['GET', 'POST', 'DELETE'])
def storage_data():
    try:
        if request.method == 'GET':
            # Получить данные
            response = requests.get(f'{WEB_MASTER_URL}/api/storage/data/raw')
        elif request.method == 'POST':
            # Сохранить данные
            data = request.json
            response = requests.post(
                f'{WEB_MASTER_URL}/api/storage/data/raw',
                json=data,
            )
        elif request.method == 'DELETE':
            # Удалить данные
            response = requests.post(f'{WEB_MASTER_URL}/api/storage/data/clear')

        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ml/train', methods=['POST'])
def train_model():
    try:
        response = requests.post(f'{WEB_MASTER_URL}/api/ml/train')
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ml/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        response = requests.post(
            f'{WEB_MASTER_URL}/api/ml/predict',
            json=data,
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/ml/model/info', methods=['GET'])
def model_info():
    try:
        response = requests.get(f'{WEB_MASTER_URL}/api/ml/model/info')
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
