from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db, Notification

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


@notifications_bp.route("", methods=["GET"])
@jwt_required()
def list_notifications():
    user_id = get_jwt_identity()
    notes = (Notification.query.filter_by(user_id=user_id)
             .order_by(Notification.created_at.desc()).all())
    return jsonify([n.to_dict() for n in notes]), 200


@notifications_bp.route("/<int:notification_id>/read", methods=["PUT"])
@jwt_required()
def mark_read(notification_id):
    note = Notification.query.get_or_404(notification_id)
    note.status = "Read"
    db.session.commit()
    return jsonify({"message": "Marked as read", "notification": note.to_dict()}), 200


@notifications_bp.route("/read-all", methods=["PUT"])
@jwt_required()
def mark_all_read():
    user_id = get_jwt_identity()
    Notification.query.filter_by(user_id=user_id, status="Unread").update({"status": "Read"})
    db.session.commit()
    return jsonify({"message": "All notifications marked as read"}), 200
