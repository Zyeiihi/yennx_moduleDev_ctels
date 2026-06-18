from flask import Flask, jsonify, send_from_directory
from internal.handler.router import api_blueprint
import os

# Cấu hình Flask nhận diện thư mục 'web' làm static folder để chứa UI
app = Flask(__name__, static_folder='web', static_url_path='')

# Đăng ký Routing Blueprint theo quy chuẩn Clean Architecture
app.register_blueprint(api_blueprint)

# ROUTE MỚI: Trả về file index.html khi người dùng truy cập vào trang chủ hoặc /web
@app.route('/')
@app.route('/web')
def serve_dashboard():
    """Phục vụ file giao diện Frontend Dashboard từ thư mục web"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint kiểm định sức khỏe phục vụ cho Docker Healthcheck"""
    return jsonify({"status": "healthy", "service": "mini-asm-python"}), 200

if __name__ == '__main__':
    print("🚀 Launching Mini ASM Python System on port 8080...")
    app.run(host='0.0.0.0', port=8080, debug=True)