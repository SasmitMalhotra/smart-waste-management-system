from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import (
    db,
    User,
    Bin,
    Collection,
    Complaint,
    CollectorLocation,
)
from utils.decorators import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.route("/dashboard", methods=["GET"])
@jwt_required()
@role_required("Admin")
def dashboard_stats():
    total_bins = Bin.query.count()
    full_bins = Bin.query.filter(
        Bin.status.in_(["Full", "Overflowing"])
    ).count()

    pending_collections = Collection.query.filter_by(
        status="Pending"
    ).count()

    pending_complaints = Complaint.query.filter_by(
        status="Pending"
    ).count()

    total_users = User.query.filter_by(role="Citizen").count()
    total_collectors = User.query.filter_by(role="Collector").count()

    zone_breakdown = (
        db.session.query(
            Bin.zone,
            db.func.avg(Bin.current_fill_level)
        )
        .group_by(Bin.zone)
        .all()
    )

    return jsonify({
        "total_bins": total_bins,
        "bins_needing_collection": full_bins,
        "pending_collections": pending_collections,
        "pending_complaints": pending_complaints,
        "total_citizens": total_users,
        "total_collectors": total_collectors,
        "zone_fill_average": [
            {
                "zone": zone,
                "average_fill_level": round(avg or 0, 1)
            }
            for zone, avg in zone_breakdown
        ],
    }), 200


@admin_bp.route("/users", methods=["GET"])
@jwt_required()
@role_required("Admin")
def list_users():
    role = request.args.get("role")

    query = User.query

    if role:
        query = query.filter_by(role=role)

    users = query.order_by(User.created_at.desc()).all()

    return jsonify([u.to_dict() for u in users]), 200


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
@role_required("Admin")
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "User removed"}), 200


# ==========================================================
# LIVE COLLECTOR TRACKING
# ==========================================================

@admin_bp.route("/collector-tracking", methods=["GET"])
@jwt_required()
@role_required("Admin")
def collector_tracking():

    collectors = User.query.filter_by(role="Collector").all()

    result = []

    for collector in collectors:

        location = (
            CollectorLocation.query
            .filter_by(collector_id=collector.id)
            .order_by(CollectorLocation.recorded_at.desc())
            .first()
        )

        current_job = (
            Collection.query
            .filter(
                Collection.collector_id == collector.id,
                Collection.status.in_(["Pending", "In Progress"])
            )
            .order_by(Collection.scheduled_date.asc())
            .first()
        )

        result.append({
            "collector": {
                "id": collector.id,
                "name": collector.full_name,
                "phone": collector.phone,
                "zone": collector.zone,
            },

            "location": location.to_dict() if location else None,

            "current_job": current_job.to_dict()
            if current_job else None,

            "completed_jobs": Collection.query.filter_by(
                collector_id=collector.id,
                status="Completed"
            ).count(),

            "pending_jobs": Collection.query.filter(
                Collection.collector_id == collector.id,
                Collection.status.in_(["Pending", "In Progress"])
            ).count(),
        })

    return jsonify(result), 200


# ==========================================================
# COLLECTOR LOCATION UPDATE
# ==========================================================

@admin_bp.route("/collector-location", methods=["POST"])
@jwt_required()
@role_required("Collector")
def update_collector_location():

    collector_id = int(get_jwt_identity())

    data = request.get_json(silent=True) or {}

    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if latitude is None or longitude is None:
        return jsonify({
            "error": "latitude and longitude are required"
        }), 400

    current_collection_id = data.get("current_collection_id")
    is_tracking = data.get("is_tracking", True)

    location = CollectorLocation(
        collector_id=collector_id,
        latitude=float(latitude),
        longitude=float(longitude),
        current_collection_id=current_collection_id,
        is_tracking=bool(is_tracking),
    )

    db.session.add(location)
    db.session.commit()

    return jsonify({
        "message": "Collector location updated",
        "location": location.to_dict()
    }), 200


# ==========================================================
# STOP TRACKING
# ==========================================================

@admin_bp.route("/collector-location/stop", methods=["POST"])
@jwt_required()
@role_required("Collector")
def stop_collector_tracking():

    collector_id = int(get_jwt_identity())

    location = (
        CollectorLocation.query
        .filter_by(collector_id=collector_id)
        .order_by(CollectorLocation.recorded_at.desc())
        .first()
    )

    if location:
        location.is_tracking = False
        db.session.commit()

    return jsonify({
        "message": "Collector tracking stopped"
    }), 200