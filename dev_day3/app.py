# FILE: app.py
import os
from flask import Flask, jsonify, send_from_directory
from internal.handler.router import api_blueprint

app = Flask(__name__, static_folder="web", static_url_path="")
app.register_blueprint(api_blueprint)


@app.route("/")
@app.route("/web")
def serve_dashboard():
    """Serve the frontend SPA from the web/ directory."""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for Docker and load balancers."""
    db_status = "ok"
    try:
        from internal.storage.database import DatabaseStorage
        DatabaseStorage()  # Will raise if DB unreachable
    except Exception as e:
        db_status = f"degraded: {str(e)}"
    return jsonify({
        "status": "healthy" if db_status == "ok" else "degraded",
        "service": "mini-asm",
        "db": db_status,
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    print(f"🚀 Mini ASM starting on port {port} (debug={debug})")
    app.run(host="0.0.0.0", port=port, debug=debug)
