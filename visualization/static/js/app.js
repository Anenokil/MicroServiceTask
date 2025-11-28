const API_BASE = '/api';
let activityLog = [];

function logActivity(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = { timestamp, message, type };
    activityLog.unshift(logEntry);

    // Ограничиваем лог последними 10 записями
    if (activityLog.length > 10) {
        activityLog = activityLog.slice(0, 10);
    }

    updateActivityLog();
}

function updateActivityLog() {
    const logHtml = activityLog.map(entry => `
        <div class="alert alert-${entry.type === 'error' ? 'danger' : 'info'} alert-dismissible fade show" role="alert">
            <small>${entry.timestamp}</small> - ${entry.message}
        </div>
    `).join('');
    $('#activity-log').html(logHtml);
}

async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/system/health`);
        const data = await response.json();

        let html = '<div class="row">';
        for (const [service, status] of Object.entries(data.status)) {
            const statusClass = status === 'healthy' ? 'status-healthy' : 
                                status === 'unhealthy' ? 'status-unhealthy' : 'status-unknown';
            html += `
                <div class="col-md-3">
                    <div class="alert ${status === 'healthy' ? 'alert-success' : 'alert-danger'}">
                        <i class="fas fa-server"></i> ${service}
                        <br>
                        <i class="fas fa-circle ${statusClass}"></i> ${status}
                    </div>
                </div>
            `;
        }
        html += '</div>';
        $('#health-status').html(html);

        logActivity('System health checked', 'info');
    } catch (error) {
        $('#health-status').html(`
            <div class="alert alert-danger">
                Error checking system health: ${error.message}
            </div>
        `);
        logActivity(`Health check failed: ${error.message}`, 'error');
    }
}

async function collectData() {
    const batchSize = $('#batch-size').val();
    try {
        const response = await fetch(`${API_BASE}/collector/batch?batch_size=${batchSize}`);
        const data = await response.json();

        // Сохраняем данные для последующего использования
        window.collectedData = data.data;

        $('#collector-result').html(`
            <div class="alert alert-success">
                <i class="fas fa-check"></i> Collected ${data.count} records
                <br>
                <small>Sample: ${JSON.stringify(data.data[0])}</small>
            </div>
        `);

        logActivity(`Collected ${data.count} data records`, 'info');
        updateCharts();
    } catch (error) {
        $('#collector-result').html(`
            <div class="alert alert-danger">
                Error collecting data: ${error.message}
            </div>
        `);
        logActivity(`Data collection failed: ${error.message}`, 'error');
    }
}

async function saveToStorage() {
    if (!window.collectedData) {
        alert('No data collected yet. Please collect data first.');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/storage/data`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data: window.collectedData })
        });
        const data = await response.json();

        $('#collector-result').append(`
            <div class="alert alert-info mt-2">
                <i class="fas fa-check"></i> ${data.count} records saved to storage
            </div>
        `);

        logActivity(`Saved ${data.count} records to storage`, 'info');
        loadStorageData();
    } catch (error) {
        $('#collector-result').append(`
            <div class="alert alert-danger mt-2">
                Error saving to storage: ${error.message}
            </div>
        `);
        logActivity(`Storage save failed: ${error.message}`, 'error');
    }
}

async function loadStorageData() {
    try {
        const response = await fetch(`${API_BASE}/storage/data`);
        const data = await response.json();

        $('#storage-info').html(`
            <div class="alert alert-info">
                Total records: ${data.data ? data.data.length : 0}
            </div>
        `);

        if (data.data && data.data.length > 0) {
            const tableHtml = `
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Features</th>
                            <th>Timestamp</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.data.slice(0, 5).map(item => `
                            <tr>
                                <td>${item.id}</td>
                                <td><small>${JSON.stringify(item.features).substring(0, 50)}...</small></td>
                                <td><small>${item.timestamp}</small></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                ${data.data.length > 5 ? `<small>Showing 5 of ${data.data.length} records</small>` : ''}
            `;
            $('#storage-data').html(tableHtml);
        } else {
            $('#storage-data').html('<div class="alert alert-warning">No data in storage</div>');
        }

        logActivity('Loaded data from storage', 'info');
    } catch (error) {
        $('#storage-info').html(`
            <div class="alert alert-danger">
                Error loading storage data: ${error.message}
            </div>
        `);
        logActivity(`Storage load failed: ${error.message}`, 'error');
    }
}

async function clearStorage() {
    if (!confirm('Are you sure you want to clear all data from storage?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/storage/data`, {
            method: 'DELETE'
        });
        const data = await response.json();

        $('#storage-info').html(`
            <div class="alert alert-success">
                <i class="fas fa-check"></i> ${data.message}
            </div>
        `);
        $('#storage-data').empty();

        logActivity('Storage cleared', 'warning');
    } catch (error) {
        $('#storage-info').html(`
            <div class="alert alert-danger">
                Error clearing storage: ${error.message}
            </div>
        `);
        logActivity(`Storage clear failed: ${error.message}`, 'error');
    }
}

async function trainModel() {
    try {
        const response = await fetch(`${API_BASE}/ml/train`, {
            method: 'POST'
        });
        const data = await response.json();

        if (data.error) {
            $('#model-info').html(`
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i> ${data.error}
                </div>
            `);
            logActivity(`Model training failed: ${data.error}`, 'error');
        } else {
            $('#model-info').html(`
                <div class="alert alert-success">
                    <i class="fas fa-check"></i> Model trained successfully!
                    <br>
                    <small>Accuracy: Train=${data.metrics.train_accuracy.toFixed(3)}, Test=${data.metrics.test_accuracy.toFixed(3)}</small>
                </div>
            `);
            logActivity('Model trained successfully', 'info');
        }
    } catch (error) {
        $('#model-info').html(`
            <div class="alert alert-danger">
                Error training model: ${error.message}
            </div>
        `);
        logActivity(`Model training failed: ${error.message}`, 'error');
    }
}

async function makePrediction() {
    const features = [
        parseFloat($('#feature1').val()),
        parseFloat($('#feature2').val()),
        parseFloat($('#feature3').val()),
        parseFloat($('#feature4').val())
    ];

    try {
        const response = await fetch(`${API_BASE}/ml/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ features: features })
        });
        const data = await response.json();

        if (data.error) {
            $('#prediction-result').html(`
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i> ${data.error}
                </div>
            `);
            logActivity(`Prediction failed: ${data.error}`, 'error');
        } else {
            $('#prediction-result').html(`
                <div class="alert alert-success">
                    <h6>Prediction Result</h6>
                    <strong>Class:</strong> ${data.predictions[0]}<br>
                    <strong>Probabilities:</strong><br>
                    ${data.class_labels.map((label, i) =>
                        `${label}: ${(data.probabilities[0][i] * 100).toFixed(2)}%`
                    ).join('<br>')}
                </div>
            `);
            logActivity(`Prediction made: class ${data.predictions[0]}`, 'info');
        }
    } catch (error) {
        $('#prediction-result').html(`
            <div class="alert alert-danger">
                Error making prediction: ${error.message}
            </div>
        `);
        logActivity(`Prediction failed: ${error.message}`, 'error');
    }
}

async function updateCharts() {
    if (!window.collectedData || window.collectedData.length === 0) {
        return;
    }

    try {
        const features = ['feature1', 'feature2', 'feature3', 'feature4'];
        const traces = features.map(feature => ({
            y: window.collectedData.map(d => d[feature]),
            name: feature,
            type: 'box'
        }));

        Plotly.newPlot('features-chart', traces, {
            title: 'Feature Distributions',
            boxmode: 'group'
        });

        const targets = window.collectedData.map(d => d.target);
        const targetCounts = {};
        targets.forEach(t => {
            targetCounts[t] = (targetCounts[t] || 0) + 1;
        });

        const targetTrace = {
            labels: Object.keys(targetCounts),
            values: Object.values(targetCounts),
            type: 'pie',
            hole: 0.4
        };

        Plotly.newPlot('predictions-chart', [targetTrace], {
            title: 'Target Class Distribution'
        });

        logActivity('Charts updated', 'info');
    } catch (error) {
        console.error('Error updating charts:', error);
        logActivity(`Chart update failed: ${error.message}`, 'error');
    }
}

// Инициализация при загрузке страницы
$(document).ready(function() {
    checkHealth();
    loadStorageData();

    setInterval(checkHealth, 30000);

    $('#batch-size').on('change', updateCharts);
});
