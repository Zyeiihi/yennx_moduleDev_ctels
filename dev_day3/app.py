from flask import Flask, jsonify
from internal.handler.router import api_blueprint

app = Flask(__name__)

# Register Routing Blueprint according to Clean Architecture standards
app.register_blueprint(api_blueprint)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint utilized by Docker Healthcheck"""
    return jsonify({"status": "healthy", "service": "mini-asm-python"}), 200

if __name__ == '__main__':
    print("🚀 Launching Mini ASM Python System on port 8080...")
    app.run(host='0.0.0.0', port=8080, debug=True)