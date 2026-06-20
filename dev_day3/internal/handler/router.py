# FILE: internal/handler/router.py
"""
Flask route definitions following Clean Architecture.
All routes delegate to service / storage layers; no business logic here.
"""
from flask import Blueprint, request, jsonify
from internal.model.asset import Asset, ScanJob
from internal.service.scan_service import ScanService

api_blueprint = Blueprint("api", __name__)

# -- Lazy-load storage so we only connect once the app is fully initialised --
_storage = None
_scan_service = None


def get_storage():
    global _storage
    if _storage is None:
        from internal.storage.database import DatabaseStorage
        _storage = DatabaseStorage()
    return _storage


def get_scan_service():
    global _scan_service
    if _scan_service is None:
        _scan_service = ScanService(storage=get_storage())
    return _scan_service


# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------

@api_blueprint.after_request
def apply_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response


@api_blueprint.route("/<path:path>", methods=["OPTIONS"])
def options_handler(path):
    return "", 200


# ---------------------------------------------------------------------------
# Asset endpoints
# ---------------------------------------------------------------------------

@api_blueprint.route("/assets", methods=["POST"])
def create_asset():
    data = request.get_json() or {}
    if not data.get("name") or not data.get("type"):
        return jsonify({"error": "Fields 'name' and 'type' are required"}), 400
    try:
        tags = data.get("tags", ["Production"])
        if isinstance(tags, str):
            tags = [tags]
        asset = Asset(data["name"], data["type"], tags=tags)
        get_storage().save_asset(asset)
        return jsonify(asset.to_dict()), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@api_blueprint.route("/assets", methods=["GET"])
def list_assets():
    return jsonify([a.to_dict() for a in get_storage().list_assets()]), 200


@api_blueprint.route("/assets/<asset_id>", methods=["GET"])
def get_asset(asset_id):
    asset = get_storage().get_asset(asset_id)
    if not asset:
        return jsonify({"error": "Asset not found"}), 404
    return jsonify(asset.to_dict()), 200


@api_blueprint.route("/assets/<asset_id>", methods=["DELETE"])
def delete_asset(asset_id):
    deleted = get_storage().delete_asset(asset_id)
    if not deleted:
        return jsonify({"error": "Asset not found"}), 404
    return jsonify({"message": "Asset deleted successfully"}), 200


# ---------------------------------------------------------------------------
# Scan job endpoints
# ---------------------------------------------------------------------------

@api_blueprint.route("/assets/<asset_id>/scan", methods=["POST"])
def start_scan_job(asset_id):
    asset = get_storage().get_asset(asset_id)
    if not asset:
        return jsonify({"error": "Asset not found"}), 404

    data = request.get_json() or {}
    scan_type = data.get("scan_type")
    if not scan_type:
        return jsonify({"error": "Field 'scan_type' is required"}), 400

    try:
        job = ScanJob(asset_id=asset_id, scan_type=scan_type)
        get_scan_service().start_scan(job)
        return jsonify(job.to_dict()), 202
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@api_blueprint.route("/scan-jobs/<job_id>", methods=["GET"])
def get_job_status(job_id):
    job = get_storage().get_job(job_id)
    if not job:
        return jsonify({"error": "Scan job not found"}), 404
    return jsonify(job.to_dict()), 200


@api_blueprint.route("/scan-jobs/<job_id>/results", methods=["GET"])
def get_job_results(job_id):
    job = get_storage().get_job(job_id)
    if not job:
        return jsonify({"error": "Scan job not found"}), 404
    return jsonify({
        "job_id": job.id,
        "scan_type": job.scan_type,
        "status": job.status,
        "results": job.results,
    }), 200


@api_blueprint.route("/assets/<asset_id>/scans", methods=["GET"])
def list_scans_for_asset(asset_id):
    jobs = get_storage().get_jobs_by_asset(asset_id)
    return jsonify([j.to_dict() for j in jobs]), 200


@api_blueprint.route("/assets/<asset_id>/results", methods=["GET"])
def get_all_results_for_asset(asset_id):
    """Aggregate all scan results for an asset across all jobs."""
    asset = get_storage().get_asset(asset_id)
    if not asset:
        return jsonify({"error": "Asset not found"}), 404
    results = get_storage().get_all_results_for_asset(asset_id)
    return jsonify({"asset_id": asset_id, "total": len(results), "results": results}), 200


# Convenience: get latest DNS/WHOIS/subdomain results for an asset
@api_blueprint.route("/assets/<asset_id>/dns", methods=["GET"])
def get_asset_dns(asset_id):
    return _get_latest_scan_result(asset_id, "dns")


@api_blueprint.route("/assets/<asset_id>/whois", methods=["GET"])
def get_asset_whois(asset_id):
    return _get_latest_scan_result(asset_id, "whois")


@api_blueprint.route("/assets/<asset_id>/subdomains", methods=["GET"])
def get_asset_subdomains(asset_id):
    return _get_latest_scan_result(asset_id, "subdomain")


def _get_latest_scan_result(asset_id: str, scan_type: str):
    jobs = get_storage().get_jobs_by_asset(asset_id)
    matching = [j for j in jobs if j.scan_type == scan_type and j.status == "completed"]
    if not matching:
        return jsonify({"error": f"No completed '{scan_type}' scan found for this asset"}), 404
    latest = max(matching, key=lambda j: j.ended_at or "")
    return jsonify({"job_id": latest.id, "scan_type": scan_type, "results": latest.results}), 200
