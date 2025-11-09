import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)


class MLService:
    def __init__(self, model_path: str):
        self.model = None
        self.model_path = model_path
        self.load_model()

    def load_model(self):
        if os.path.exists(self.model_path):
            try:
                model_data = joblib.load(self.model_path)
                self.model = model_data['model']
                print('Model is loaded from', self.model_path)
            except Exception as e:
                print('Model loading error:', e)
                self.model = None
        else:
            print('No model file')
            self.model = None

    def save_model(self, metadata=None):
        os.makedirs('ml_model', exist_ok=True)

        model_data = {
            'model': self.model,
        }

        joblib.dump(model_data, self.model_path)
        print(f'Model is saved to "{self.model_path}"')

    def prepare_features(self, raw_data):
        features = []
        targets = []

        for item in raw_data:
            if isinstance(item['features'], dict):
                feature_vector = [
                    item['features'].get('feature1', 0),
                    item['features'].get('feature2', 0),
                    item['features'].get('feature3', 0),
                    item['features'].get('feature4', 0)
                ]
                target = item['features'].get('target', 0)
            else:
                feature_vector = [
                    item.get('feature1', 0),
                    item.get('feature2', 0),
                    item.get('feature3', 0),
                    item.get('feature4', 0)
                ]
                target = item.get('target', 0)

            features.append(feature_vector)
            targets.append(target)

        return np.array(features), np.array(targets)

    def train_model(self, data):
        try:
            x, y = self.prepare_features(data)

            if len(x) == 0:
                raise ValueError('No features extracted from data')

            x_train, x_test, y_train, y_test = train_test_split(
                x, y, test_size=0.2, random_state=42
            )

            self.model = RandomForestClassifier(
                n_estimators=100,
                random_state=42,
                max_depth=10,
            )
            self.model.fit(x_train, y_train)

            train_score = self.model.score(x_train, y_train)
            test_score = self.model.score(x_test, y_test)

            metadata = {
                'training_date': pd.Timestamp.now().isoformat(),
                'train_accuracy': float(train_score),
                'test_accuracy': float(test_score),
                'n_samples': len(x),
                'model_type': 'RandomForestClassifier',
                'feature_count': x.shape[1],
                'classes': self.model.classes_.tolist(),
            }

            self.save_model(metadata)
            return metadata

        except Exception as e:
            print(f'Training error: {e}')
            raise

    def predict(self, features):
        if self.model is None:
            raise Exception('Model not trained. Please train the model first.')

        if isinstance(features, list):
            features = np.array(features)

        predictions = self.model.predict(features)
        probabilities = self.model.predict_proba(features)

        return {
            'predictions': predictions.tolist(),
            'probabilities': probabilities.tolist(),
            'class_labels': self.model.classes_.tolist(),
        }


ml_service = MLService('ml_model/model.joblib')


@app.route('/train', methods=['POST'])
def train():
    try:
        # Получение данных из storage
        storage_url = os.getenv('STORAGE_SERVICE_URL', 'http://storage:5000')
        response = requests.get(f'{storage_url}/data/raw')

        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch training data from storage'}), 500

        data = response.json().get('data', [])

        if not data:
            return jsonify({'error': 'No training data available'}), 400

        # Обучение модели
        metrics = ml_service.train_model(data)

        return jsonify({
            'status': 'success',
            'message': 'Model trained successfully',
            'metrics': metrics,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/predict', methods=['POST'])
def predict():
    try:
        features = request.json.get('features', [])

        if not features:
            return jsonify({'error': 'No features provided'}), 400

        if isinstance(features[0], (int, float)):
            features = [features]

        result = ml_service.predict(features)

        # Сохранение результатов в storage
        storage_url = os.getenv('STORAGE_SERVICE_URL', 'http://storage:5000')

        processed_data = []
        for i, feat in enumerate(features):
            processed_data.append({
                'features': {
                    'feature1': feat[0] if len(feat) > 0 else 0,
                    'feature2': feat[1] if len(feat) > 1 else 0,
                    'feature3': feat[2] if len(feat) > 2 else 0,
                    'feature4': feat[3] if len(feat) > 3 else 0,
                },
                'predictions': {
                    'class': result['predictions'][i],
                    'probabilities': dict(zip(result['class_labels'], result['probabilities'][i]))
                }
            })

        requests.post(f'{storage_url}/data/processed', json={
            'data': processed_data
        })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/model/info', methods=['GET'])
def model_info():
    if ml_service.model is None:
        return jsonify({'status': 'no_model', 'message': 'Model not trained'})

    try:
        model_data = joblib.load(ml_service.model_path)
        return jsonify({
            'status': 'loaded',
            'metadata': model_data.get('metadata', {}),
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'model_loaded': ml_service.model is not None})


@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'service': 'ML Service',
        'status': 'healthy',
        'model_loaded': ml_service.model is not None,
        'endpoints': {
            '/train': 'POST - обучить модель',
            '/predict': 'POST - сделать предсказание',
            '/model/info': 'GET - информация о модели',
            '/health': 'GET - проверка здоровья',
        }
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
