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
# ZONE HELPER
# ==========================================================

def normalize_zone(zone):
    """
    Converts:
        A
        Zone A
        zone a
        Zone Zone A

    into:
        A
    """

    value = str(zone or "").strip().upper()

    while value.startswith("ZONE "):
        value = value[5:].strip()

    return value


# ==========================================================
# GET COLLECTIONS
# ==========================================================

@collections_bp.route("", methods=["GET"])
@jwt_required()
def list_collections():

    claims = get_jwt()

    status_filter = request.args.get("status")

    # ======================================================
    # COLLECTOR VIEW
    # ======================================================

    if claims.get("role") == "Collector":

        collector_id = int(get_jwt_identity())

        jobs = (
            Collection.query
            .filter_by(collector_id=collector_id)
            .order_by(Collection.scheduled_date.asc())
            .all()
        )

        results = []

        for job in jobs:

            data = job.to_dict()

            # ------------------------------------------------
            # Display Planned below 75%.
            #
            # IMPORTANT:
            # The database still stores "Pending".
            # "Planned" exists only in the API response.
            # ------------------------------------------------

            if (
                job.status == "Pending"
                and job.bin
                and job.bin.current_fill_level < 75
            ):
                data["status"] = "Planned"

            if status_filter:

                if data["status"] != status_filter:
                    continue

            results.append(data)

        return jsonify(results), 200

    # ======================================================
    # ADMIN VIEW
    # ======================================================

    bins = (
        Bin.query
        .order_by(Bin.id.asc())
        .all()
    )

    # ------------------------------------------------------
    # Make sure every bin has an active collection job.
    #
    # Existing completed/missed jobs are kept as history.
    # A new Pending job is created only when there is no
    # active Pending/In Progress job for that bin.
    # ------------------------------------------------------

    changed = False

    for bin_obj in bins:

        active_job = (
            Collection.query
            .filter(
                Collection.bin_id == bin_obj.id,
                Collection.status.in_(
                    ["Pending", "In Progress"]
                )
            )
            .order_by(Collection.id.desc())
            .first()
        )

        if not active_job:

            new_job = Collection(
                bin_id=bin_obj.id,
                collector_id=None,
                scheduled_date=datetime.utcnow(),
                status="Pending",
                notes="Planned collection"
            )

            db.session.add(new_job)

            changed = True

    if changed:
        db.session.commit()

    # ------------------------------------------------------
    # Get active jobs for all bins.
    # ------------------------------------------------------

    active_jobs = (
        Collection.query
        .filter(
            Collection.status.in_(
                ["Pending", "In Progress"]
            )
        )
        .order_by(Collection.scheduled_date.asc())
        .all()
    )

    results = []

    for job in active_jobs:

        if not job.bin:
            continue

        data = job.to_dict()

        # --------------------------------------------------
        # 75% THRESHOLD
        #
        # Below 75% = Planned
        # 75% and above = Pending
        #
        # "Planned" is only a display value.
        # The database enum remains valid.
        # --------------------------------------------------

        if (
            job.status == "Pending"
            and job.bin.current_fill_level < 75
        ):
            data["status"] = "Planned"

        else:
            data["status"] = job.status

        if status_filter:

            if data["status"] != status_filter:
                continue

        results.append(data)

    return jsonify(results), 200


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

    # ------------------------------------------------------
    # VALIDATE COLLECTOR
    # ------------------------------------------------------

    if collector_id:

        collector = User.query.filter_by(
            id=collector_id,
            role="Collector"
        ).first()

        if not collector:

            return jsonify({
                "error": "Invalid collector"
            }), 400

        # Collector must belong to same zone as bin
        if normalize_zone(collector.zone) != normalize_zone(bin_obj.zone):

            return jsonify({
                "error":
                    "Collector must belong to the same zone as the bin"
            }), 400

    # ------------------------------------------------------
    # CREATE JOB
    # ------------------------------------------------------

    job = Collection(
        bin_id=bin_obj.id,
        collector_id=collector_id,
        scheduled_date=scheduled_date,
        notes=data.get("notes")
    )

    db.session.add(job)

    # ------------------------------------------------------
    # NOTIFY COLLECTOR
    # ------------------------------------------------------

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

        # --------------------------------------------------
        # Do not create duplicate active jobs.
        # --------------------------------------------------

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

            # Make sure a pending job has the correct note.
            if active_job.status == "Pending":

                active_job.notes = (
                    "Auto-scheduled: bin near capacity"
                )

            continue

        # --------------------------------------------------
        # Create a new pending job.
        # --------------------------------------------------

        job = Collection(
            bin_id=bin_obj.id,
            collector_id=None,
            scheduled_date=datetime.utcnow(),
            status="Pending",
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

        # "Planned" is a display-only status.
        # Never store it in the database enum.
        if new_status == "Planned":

            new_status = "Pending"

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
        # COLLECTION REOPENED / MISSED / PENDING
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

            # Collector must belong to same zone as bin
            if normalize_zone(collector.zone) != normalize_zone(job.bin.zone):

                return jsonify({
                    "error":
                        "Collector must belong to the same zone as the bin"
                }), 400

        job.collector_id = collector_id

        # --------------------------------------------------
        # NOTIFY COLLECTOR
        # --------------------------------------------------

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