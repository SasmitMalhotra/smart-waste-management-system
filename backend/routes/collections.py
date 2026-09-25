from datetime import datetime

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    get_jwt
)

from models import (
    db,
    Collection,
    Bin,
    Notification,
    User
)

from utils.decorators import role_required


collections_bp = Blueprint(
    "collections",
    __name__,
    url_prefix="/api/collections"
)


# ==========================================================
# GET COLLECTIONS
# ==========================================================

@collections_bp.route("", methods=["GET"])
@jwt_required()
def list_collections():

    claims = get_jwt()

    query = Collection.query

    status = request.args.get("status")

    if status:
        query = query.filter_by(status=status)

    # Collectors only see their own assigned collections
    if claims.get("role") == "Collector":

        collector_id = int(get_jwt_identity())

        query = query.filter_by(
            collector_id=collector_id
        )

    jobs = (
        query
        .order_by(Collection.scheduled_date.asc())
        .all()
    )

    return jsonify(
        [collection.to_dict() for collection in jobs]
    ), 200


# ==========================================================
# CREATE COLLECTION
# ADMIN ONLY
# ==========================================================

@collections_bp.route("", methods=["POST"])
@jwt_required()
@role_required("Admin")
def create_collection():

    data = request.get_json(force=True) or {}

    if not data.get("bin_id"):
        return jsonify({
            "error": "bin_id is required"
        }), 400

    if not data.get("scheduled_date"):
        return jsonify({
            "error": "scheduled_date is required"
        }), 400

    bin_obj = Bin.query.get_or_404(
        data["bin_id"]
    )

    try:

        scheduled_date = datetime.fromisoformat(
            data["scheduled_date"]
        )

    except ValueError:

        return jsonify({
            "error": "Invalid scheduled_date format"
        }), 400

    collector_id = data.get("collector_id")

    if collector_id:

        collector = User.query.filter_by(
            id=collector_id,
            role="Collector"
        ).first()

        if not collector:

            return jsonify({
                "error": "Invalid collector"
            }), 400

    job = Collection(
        bin_id=bin_obj.id,
        collector_id=collector_id,
        scheduled_date=scheduled_date,
        notes=data.get("notes")
    )

    db.session.add(job)

    # Notify collector
    if collector_id:

        db.session.add(
            Notification(
                user_id=collector_id,
                title="New collection assigned",
                message=(
                    f"You've been assigned to collect "
                    f"bin {bin_obj.bin_code} "
                    f"at {bin_obj.location}."
                )
            )
        )

    db.session.commit()

    return jsonify({
        "message": "Collection scheduled",
        "collection": job.to_dict()
    }), 201


# ==========================================================
# AUTOMATICALLY SCHEDULE FULL BINS
# ADMIN ONLY
# ==========================================================

@collections_bp.route(
    "/auto-schedule",
    methods=["POST"]
)
@jwt_required()
@role_required("Admin")
def auto_schedule():

    threshold = current_app.config[
        "BIN_FULL_THRESHOLD"
    ]

    full_bins = (
        Bin.query
        .filter(
            Bin.current_fill_level >= threshold
        )
        .all()
    )

    created = []

    for bin_obj in full_bins:

        # Do not create duplicate active jobs
        active_job = (
            Collection.query
            .filter(
                Collection.bin_id == bin_obj.id,
                Collection.status.in_(
                    ["Pending", "In Progress"]
                )
            )
            .first()
        )

        if active_job:
            continue

        job = Collection(
            bin_id=bin_obj.id,
            scheduled_date=datetime.utcnow(),
            notes="Auto-scheduled: bin near capacity"
        )

        db.session.add(job)

        created.append(job)

    db.session.commit()

    return jsonify({
        "message":
            f"{len(created)} collection(s) scheduled",

        "collections":
            [job.to_dict() for job in created]

    }), 201


# ==========================================================
# UPDATE COLLECTION
# ADMIN + ASSIGNED COLLECTOR
# ==========================================================

@collections_bp.route(
    "/<int:collection_id>",
    methods=["PUT"]
)
@jwt_required()
@role_required("Admin", "Collector")
def update_collection(collection_id):

    job = Collection.query.get_or_404(
        collection_id
    )

    claims = get_jwt()

    role = claims.get("role")

    current_user_id = int(
        get_jwt_identity()
    )

    # ------------------------------------------------------
    # SECURITY
    # ------------------------------------------------------

    if role == "Collector":

        if job.collector_id != current_user_id:

            return jsonify({
                "error":
                    "You can only update "
                    "your own assigned collections"
            }), 403

    data = request.get_json(
        force=True
    ) or {}

    # ------------------------------------------------------
    # UPDATE STATUS
    # ------------------------------------------------------

    if "status" in data:

        new_status = data["status"]

        allowed_statuses = [
            "Pending",
            "In Progress",
            "Completed",
            "Missed"
        ]

        if new_status not in allowed_statuses:

            return jsonify({
                "error":
                    "Invalid collection status"
            }), 400

        job.status = new_status

        # --------------------------------------------------
        # COLLECTION COMPLETED
        # --------------------------------------------------

        if new_status == "Completed":

            job.completed_at = datetime.utcnow()

            if job.bin:

                # Empty the physical bin
                job.bin.current_fill_level = 0

                job.bin.status = "Empty"

                job.bin.last_collected_at = (
                    datetime.utcnow()
                )

        # --------------------------------------------------
        # COLLECTION STARTED
        # --------------------------------------------------

        elif new_status == "In Progress":

            job.completed_at = None

        # --------------------------------------------------
        # COLLECTION REOPENED / MISSED
        # --------------------------------------------------

        else:

            job.completed_at = None

    # ------------------------------------------------------
    # UPDATE COLLECTOR
    # ------------------------------------------------------

    if "collector_id" in data:

        if role != "Admin":

            return jsonify({
                "error":
                    "Only an admin can "
                    "reassign collections"
            }), 403

        collector_id = data["collector_id"]

        if collector_id is not None:

            collector = User.query.filter_by(
                id=collector_id,
                role="Collector"
            ).first()

            if not collector:

                return jsonify({
                    "error":
                        "Invalid collector"
                }), 400

        job.collector_id = collector_id

        # Notify newly assigned collector
        if collector_id:

            db.session.add(
                Notification(
                    user_id=collector_id,
                    title="Collection assigned",
                    message=(
                        f"You have been assigned "
                        f"bin {job.bin.bin_code} "
                        f"at {job.bin.location}."
                    )
                )
            )

    # ------------------------------------------------------
    # UPDATE NOTES
    # ------------------------------------------------------

    if "notes" in data:

        job.notes = data["notes"]

    db.session.commit()

    return jsonify({
        "message":
            "Collection updated",

        "collection":
            job.to_dict()

    }), 200


# ==========================================================
# DELETE COLLECTION HISTORY
# ADMIN ONLY
# ==========================================================

@collections_bp.route(
    "/<int:collection_id>",
    methods=["DELETE"]
)
@jwt_required()
@role_required("Admin")
def delete_collection_history(collection_id):

    job = Collection.query.get_or_404(
        collection_id
    )

    # Only historical jobs can be deleted
    if job.status not in [
        "Completed",
        "Missed"
    ]:

        return jsonify({
            "error":
                "Only completed or missed "
                "collection history can be deleted"
        }), 400

    db.session.delete(job)

    db.session.commit()

    return jsonify({
        "message":
            "Collection history deleted successfully"
    }), 200