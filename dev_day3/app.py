from flask import Flask, jsonify
from internal.handler.router import api_blueprint

app = Flask(__name__)

# Đăng ký Routing Blueprint theo quy chuẩn Clean Architecture
app.register_blueprint(api_blueprint)

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint kiểm định sức khỏe phục vụ cho Docker Healthcheck"""
    return jsonify({"status": "healthy", "service": "mini-asm-python"}), 200

if __name__ == '__main__':
    print("🚀 Khởi chạy hệ thống Python Mini ASM tại cổng 8080...")
    app.run(host='0.0.0.0', port=8080, debug=True)