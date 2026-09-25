from flask import Flask, jsonify, send_from_directory
import os
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config
from models import db, bcrypt

from routes.auth import auth_bp
from routes.bins import bins_bp
from routes.collections import collections_bp
from routes.complaints import complaints_bp
from routes.notifications import notifications_bp
from routes.admin import admin_bp


def create_app(config_class=Config):

    # Frontend folder
    frontend_folder = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "frontend"
    )

    app = Flask(
        __name__,
        static_folder=frontend_folder,
        static_url_path=""
    )

    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    JWTManager(app)
    CORS(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(bins_bp)
    app.register_blueprint(collections_bp)
    app.register_blueprint(complaints_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(admin_bp)

    # Serve frontend
    @app.route("/")
    def index():
        return send_from_directory(frontend_folder, "index.html")

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "ok",
            "service": "Smart Waste Management System API"
        }), 200

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal server error"}), 500

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)