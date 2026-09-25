import random
from datetime import datetime

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required

from models import (
    db,
    Bin,
    SensorLog,
    Notification,
    User,
    Collection
)

from utils.decorators import role_required


bins_bp = Blueprint(
    "bins",
    __name__,
    url_prefix="/api/bins"
)


# ==========================================================
# NORMALIZE ZONE
# ==========================================================

def normalize_zone(zone):

    value = str(zone or "").strip().upper()

    while value.startswith("ZONE "):
        value = value[5:].strip()

    return value


# ==========================================================
# NOTIFY ADMINS AND COLLECTORS
# ==========================================================

def _notify_admins_and_collectors(
    title,
    message
):

    recipients = User.query.filter(
        User.role.in_(
            ["Admin", "Collector"]
        )
    ).all()

    for recipient in recipients:

        db.session.add(
            Notification(
                user_id=recipient.id,
                title=title,
                message=message
            )
        )


# ==========================================================
# GET ALL BINS
# ==========================================================

@bins_bp.route("", methods=["GET"])
@jwt_required()
def list_bins():

    zone = request.args.get("zone")
    status = request.args.get("status")
    waste_type = request.args.get("waste_type")

    query = Bin.query

    if zone:

        query = query.filter_by(
            zone=zone
        )

    if status:

        query = query.filter_by(
            status=status
        )

    if waste_type:

        query = query.filter_by(
            waste_type=waste_type
        )

    bins = (
        query
        .order_by(
            Bin.current_fill_level.desc()
        )
        .all()
    )

    return jsonify(
        [b.to_dict() for b in bins]
    ), 200


# ==========================================================
# GET SINGLE BIN
# ==========================================================

@bins_bp.route(
    "/<int:bin_id>",
    methods=["GET"]
)
@jwt_required()
def get_bin(bin_id):

    b = Bin.query.get_or_404(
        bin_id
    )

    return jsonify(
        b.to_dict()
    ), 200


# ==========================================================
# CREATE BIN
# ADMIN ONLY
# ==========================================================

@bins_bp.route("", methods=["POST"])
@jwt_required()
@role_required("Admin")
def create_bin():

    data = request.get_json(
        force=True
    ) or {}

    required = [
        "bin_code",
        "location",
        "zone"
    ]

    missing = [
        field
        for field in required
        if not data.get(field)
    ]

    if missing:

        return jsonify({
            "error":
                f"Missing fields: {', '.join(missing)}"
        }), 400

    if Bin.query.filter_by(
        bin_code=data["bin_code"]
    ).first():

        return jsonify({
            "error":
                "A bin with this code already exists"
        }), 409

    b = Bin(

        bin_code=data["bin_code"],

        location=data["location"],

        latitude=data.get(
            "latitude"
        ),

        longitude=data.get(
            "longitude"
        ),

        zone=data["zone"],

        capacity_liters=data.get(
            "capacity_liters",
            100
        ),

        waste_type=data.get(
            "waste_type",
            "General"
        ),

        current_fill_level=data.get(
            "current_fill_level",
            0
        )

    )

    b.recompute_status(
        current_app.config[
            "BIN_WARNING_THRESHOLD"
        ],
        current_app.config[
            "BIN_FULL_THRESHOLD"
        ]
    )

    db.session.add(b)

    db.session.commit()

    return jsonify({

        "message":
            "Bin created",

        "bin":
            b.to_dict()

    }), 201


# ==========================================================
# UPDATE BIN
# ADMIN ONLY
# ==========================================================

@bins_bp.route(
    "/<int:bin_id>",
    methods=["PUT"]
)
@jwt_required()
@role_required("Admin")
def update_bin(bin_id):

    b = Bin.query.get_or_404(
        bin_id
    )

    data = request.get_json(
        force=True
    ) or {}

    for field in (
        "location",
        "latitude",
        "longitude",
        "zone",
        "capacity_liters",
        "waste_type"
    ):

        if field in data:

            setattr(
                b,
                field,
                data[field]
            )

    db.session.commit()

    return jsonify({

        "message":
            "Bin updated",

        "bin":
            b.to_dict()

    }), 200


# ==========================================================
# DELETE BIN
# ADMIN ONLY
# ==========================================================

@bins_bp.route(
    "/<int:bin_id>",
    methods=["DELETE"]
)
@jwt_required()
@role_required("Admin")
def delete_bin(bin_id):

    b = Bin.query.get_or_404(
        bin_id
    )

    db.session.delete(b)

    db.session.commit()

    return jsonify({
        "message":
            "Bin deleted"
    }), 200


# ==========================================================
# SENSOR UPDATE
# ==========================================================

@bins_bp.route(
    "/<int:bin_id>/sensor-update",
    methods=["POST"]
)
@jwt_required()
def sensor_update(bin_id):

    b = Bin.query.get_or_404(
        bin_id
    )

    data = request.get_json(
        silent=True
    ) or {}

    fill_level = data.get(
        "fill_level"
    )

    # Simulate sensor when no value supplied
    if fill_level is None:

        fill_level = min(
            100,
            b.current_fill_level
            + random.randint(5, 25)
        )

    fill_level = max(
        0,
        min(
            100,
            int(fill_level)
        )
    )

    was_below_threshold = (
        b.current_fill_level
        < current_app.config[
            "BIN_FULL_THRESHOLD"
        ]
    )

    # Update fill level
    b.current_fill_level = fill_level

    # Recalculate status
    b.recompute_status(
        current_app.config[
            "BIN_WARNING_THRESHOLD"
        ],
        current_app.config[
            "BIN_FULL_THRESHOLD"
        ]
    )

    # Store sensor reading
    db.session.add(
        SensorLog(
            bin_id=b.id,
            fill_level=fill_level
        )
    )

    # ======================================================
    # NOTIFICATION
    # ======================================================

    if (
        was_below_threshold
        and
        fill_level >= current_app.config[
            "BIN_FULL_THRESHOLD"
        ]
    ):

        _notify_admins_and_collectors(

            "Bin nearing capacity",

            (
                f"Bin {b.bin_code} "
                f"at {b.location} "
                f"is at {fill_level}% "
                f"and needs collection."
            )

        )

    # ======================================================
    # AUTOMATIC COLLECTION SCHEDULING
    # ======================================================

    if fill_level >= current_app.config[
        "BIN_FULL_THRESHOLD"
    ]:

        active_job = (
            Collection.query
            .filter(
                Collection.bin_id == b.id,

                Collection.status.in_(
                    [
                        "Pending",
                        "In Progress"
                    ]
                )
            )
            .first()
        )

        # Prevent duplicate jobs
        if not active_job:

            db.session.add(
                Collection(

                    bin_id=b.id,

                    collector_id=None,

                    scheduled_date=datetime.utcnow(),

                    notes=(
                        "Auto-scheduled: "
                        "bin near capacity"
                    )

                )
            )

    # Save everything
    db.session.commit()

    return jsonify({

        "message":
            "Sensor reading recorded",

        "bin":
            b.to_dict()

    }), 200


# ==========================================================
# MARK BIN COLLECTED
# ADMIN + COLLECTOR
# ==========================================================

@bins_bp.route(
    "/<int:bin_id>/collected",
    methods=["POST"]
)
@jwt_required()
@role_required(
    "Admin",
    "Collector"
)
def mark_collected(bin_id):

    b = Bin.query.get_or_404(
        bin_id
    )

    b.current_fill_level = 0

    b.status = "Empty"

    b.last_collected_at = (
        datetime.utcnow()
    )

    db.session.add(
        SensorLog(
            bin_id=b.id,
            fill_level=0
        )
    )

    db.session.commit()

    return jsonify({

        "message":
            "Bin marked as collected",

        "bin":
            b.to_dict()

    }), 200


# ==========================================================
# BIN SENSOR HISTORY
# ==========================================================

@bins_bp.route(
    "/<int:bin_id>/history",
    methods=["GET"]
)
@jwt_required()
def bin_history(bin_id):

    Bin.query.get_or_404(
        bin_id
    )

    logs = (
        SensorLog.query
        .filter_by(
            bin_id=bin_id
        )
        .order_by(
            SensorLog.recorded_at.desc()
        )
        .limit(50)
        .all()
    )

    return jsonify(
        [
            log.to_dict()
            for log in logs
        ]
    ), 200