from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from models import db, Complaint, Notification, User
from utils.decorators import role_required

complaints_bp = Blueprint("complaints", __name__, url_prefix="/api/complaints")


@complaints_bp.route("", methods=["GET"])
@jwt_required()
def list_complaints():
    claims = get_jwt()
    query = Complaint.query

    status = request.args.get("status")
    if status:
        query = query.filter_by(status=status)

    if claims.get("role") == "Citizen":
        query = query.filter_by(user_id=int(get_jwt_identity()))

    complaints = query.order_by(Complaint.reported_at.desc()).all()
    return jsonify([c.to_dict() for c in complaints]), 200


@complaints_bp.route("", methods=["POST"])
@jwt_required()
def create_complaint():
    user_id = get_jwt_identity()
    data = request.get_json(force=True) or {}

    if not data.get("reason"):
        return jsonify({"error": "reason is required"}), 400

    complaint = Complaint(
        user_id=user_id,
        bin_id=data.get("bin_id"),
        reason=data["reason"],
    )
    db.session.add(complaint)

    for admin in User.query.filter_by(role="Admin").all():
        db.session.add(Notification(
            user_id=admin.id,
            title="New complaint filed",
            message=f"A new complaint was submitted: {data['reason'][:80]}",
        ))

    db.session.commit()
    return jsonify({"message": "Complaint submitted", "complaint": complaint.to_dict()}), 201


@complaints_bp.route("/<int:complaint_id>", methods=["PUT"])
@jwt_required()
@role_required("Admin")
def update_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    data = request.get_json(force=True) or {}

    if "status" in data:
        complaint.status = data["status"]
        if data["status"] == "Resolved":
            complaint.resolved_at = datetime.utcnow()
            db.session.add(Notification(
                user_id=complaint.user_id,
                title="Your complaint was resolved",
                message=f"Complaint #{complaint.id} has been marked as resolved.",
            ))

    db.session.commit()
    return jsonify({"message": "Complaint updated", "complaint": complaint.to_dict()}), 200
