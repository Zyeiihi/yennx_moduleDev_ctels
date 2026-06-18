from flask import Blueprint, request, jsonify
from internal.model.asset import Asset, ScanJob
from internal.storage.memory import db
from internal.service.scan_service import ScanService

api_blueprint = Blueprint('api', __name__)
scan_service = ScanService()

# BÀI 3.1: CORS MIDDLEWARE THỦ CÔNG (Được kích hoạt sau mỗi Request)
@api_blueprint.after_request
def apply_cors_middleware(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
    return response

# Xử lý các request OPTIONS preflight tự động
@api_blueprint.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    return '', 200

# CÁC ENDPOINT QUẢN LÝ TÀI SẢN (ASSETS)
@api_blueprint.route('/assets', methods=['POST'])
def create_asset():
    data = request.get_json() or {}
    if not data.get('name') or not data.get('type'):
        return jsonify({"error": "Vui lòng nhập đầy đủ thuộc tính name và type"}), 400
    try:
        # BÀI 6.2 BONUS: Lấy mảng tags từ frontend truyền lên, mặc định là ["Production"]
        tags = data.get('tags', ['Production'])
        if isinstance(tags, str):  # Nếu lỡ truyền dạng chuỗi "Critical", tự chuyển thành mảng
            tags = [tags]

        # Truyền thêm trường tags vào khởi tạo Asset
        new_asset = Asset(data['name'], data['type'], tags=tags)
        db.save_asset(new_asset)
        return jsonify(new_asset.to_dict()), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@api_blueprint.route('/assets', methods=['GET'])
def list_assets():
    return jsonify([asset.to_dict() for asset in db.list_assets()]), 200

# BÀI 1: API ĐIỀU HƯỚNG VÀ KIỂM TRA TRẠNG THÁI QUÉT
@api_blueprint.route('/assets/<id>/scan', methods=['POST'])
def start_scan_job(id):
    asset = db.get_asset(id)
    if not asset:
        return jsonify({"error": "Không tìm thấy tài sản này hệ thống"}), 404
    
    data = request.get_json() or {}
    scan_type = data.get('scan_type')
    if not scan_type:
        return jsonify({"error": "Thuộc tính scan_type là bắt buộc"}), 400

    try:
        job = ScanJob(asset_id=id, scan_type=scan_type)
        # Gọi tầng Service để chạy ngầm tiến trình mạng
        scan_service.start_scan(job)
        return jsonify(job.to_dict()), 202
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@api_blueprint.route('/scan-jobs/<id>', methods=['GET'])
def get_job_status(id):
    job = db.get_job(id)
    if not job:
        return jsonify({"error": "Không thấy thông tin Job này"}), 404
    return jsonify(job.to_dict()), 200

@api_blueprint.route('/scan-jobs/<id>/results', methods=['GET'])
def get_job_results(id):
    job = db.get_job(id)
    if not job:
        return jsonify({"error": "Không thấy thông tin Job này"}), 404
    return jsonify({
        "job_id": job.id,
        "scan_type": job.scan_type,
        "results": job.results
    }), 200

@api_blueprint.route('/assets/<id>/scans', methods=['GET'])
def list_scans_for_asset(id):
    jobs = db.get_jobs_by_asset(id)
    return jsonify([j.to_dict() for j in jobs]), 200

