import time
import logging
import sys
import traceback
from flask import Flask, g, request, jsonify
from prometheus_flask_exporter import PrometheusMetrics
from pythonjsonlogger import jsonlogger
from routes import flags_bp

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Logging Setup
logger = logging.getLogger(__name__)
logHandler = logging.StreamHandler(sys.stdout)
logHandler.setFormatter(jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(logHandler)

@app.before_request
def start_timer():
    g.start_time = time.time()

@app.after_request
def log_request(response):
    latency = int((time.time() - g.start_time) * 1000)
    logger.info({"event": "api_request", "path": request.path, "latency_ms": latency})
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    # Capture the full stack trace
    tb = traceback.format_exc()
    
    logger.error({
        "event": "unhandled_exception",
        "error_type": type(e).__name__,
        "error_message": str(e),
        "traceback": tb,
        "path": request.path,
        "method": request.method,
        "client_ip": request.remote_addr
    })
    
    # Return a 500 response
    return jsonify({
        "error": "Internal Server Error", 
        "message": "An unexpected error occurred"
    }), 500

app.register_blueprint(flags_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)