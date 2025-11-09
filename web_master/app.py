import os
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

SERVICES = {
    'collector': os.getenv('COLLECTOR_URL', 'http://collector:5000'),
    'storage': os.getenv('STORAGE_URL', 'http://storage:5000'),
    'ml_service': os.getenv('ML_SERVICE_URL', 'http://ml_service:5000')
}


def make_service_request(service, endpoint, method='GET', data=None):
    url = f'{SERVICES[service]}/{endpoint}'

    try:
        if method == 'GET':
            response = requests.get(url, params=request.args)
        elif method == 'POST':
            if data is not None:
                json_data = data
            elif request.is_json:
                json_data = request.json
            else:
                json_data = None
            response = requests.post(url, json=json_data)
        else:
            return {'error': f'Method {method} not supported'}, 405

        try:
            return response.json(), response.status_code
        except ValueError:
            return response.text, response.status_code

    except requests.exceptions.RequestException as e:
        return {'error': f'Service {service} unavailable: {str(e)}'}, 503


@app.route('/api/collector/<path:endpoint>', methods=['GET', 'POST'])
def collector_proxy(endpoint):
    data = None
    if request.method == 'POST' and request.is_json:
        data = request.json
    result, status_code = make_service_request('collector', endpoint, request.method, data)
    return jsonify(result), status_code


@app.route('/api/storage/<path:endpoint>', methods=['GET', 'POST'])
def storage_proxy(endpoint):
    data = None
    if request.method == 'POST' and request.is_json:
        data = request.json
    result, status_code = make_service_request('storage', endpoint, request.method, data)
    return jsonify(result), status_code


@app.route('/api/ml/<path:endpoint>', methods=['GET', 'POST'])
def ml_proxy(endpoint):
    data = None
    if request.method == 'POST' and request.is_json:
        data = request.json
    result, status_code = make_service_request('ml_service', endpoint, request.method, data)
    return jsonify(result), status_code


@app.route('/system/health')
def system_health():
    health_status = {}

    for service, url in SERVICES.items():
        try:
            response = requests.get(f'{url}/health', timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                health_status[service] = health_data.get('status', 'healthy')
            else:
                health_status[service] = 'unhealthy'
        except requests.exceptions.RequestException:
            health_status[service] = 'unavailable'
        except Exception as e:
            health_status[service] = f'error: {str(e)}'

    return jsonify({'status': health_status})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
