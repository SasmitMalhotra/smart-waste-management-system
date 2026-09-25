from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(db.Model):
    """Citizens, waste collectors, and administrators."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    role = db.Column(
        db.Enum(
            "Citizen",
            "Collector",
            "Admin",
            name="user_role"
        ),
        default="Citizen",
        nullable=False
    )

    address = db.Column(db.String(255), nullable=True)
    zone = db.Column(db.String(100), nullable=True)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


    complaints = db.relationship(
        "Complaint",
        backref="reporter",
        lazy=True,
        foreign_keys="Complaint.user_id"
    )

    notifications = db.relationship(
        "Notification",
        backref="user",
        lazy=True
    )

    collections = db.relationship(
        "Collection",
        backref="collector",
        lazy=True,
        foreign_keys="Collection.collector_id"
    )


    def set_password(self, raw_password):

        self.password = (
            bcrypt
            .generate_password_hash(raw_password)
            .decode("utf-8")
        )


    def check_password(self, raw_password):

        return bcrypt.check_password_hash(
            self.password,
            raw_password
        )


    def to_dict(self):

        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "address": self.address,
            "zone": self.zone,
            "created_at":
                self.created_at.isoformat()
                if self.created_at
                else None,
        }


class WasteCategory(db.Model):

    __tablename__ = "waste_categories"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    category_name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=True
    )


    def to_dict(self):

        return {
            "id": self.id,
            "category_name": self.category_name,
            "description": self.description
        }


class Bin(db.Model):
    """A physical smart waste bin fitted with a simulated fill-level sensor."""

    __tablename__ = "bins"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    bin_code = db.Column(
        db.String(30),
        unique=True,
        nullable=False
    )

    location = db.Column(
        db.String(200),
        nullable=False
    )

    latitude = db.Column(
        db.Float,
        nullable=True
    )

    longitude = db.Column(
        db.Float,
        nullable=True
    )

    zone = db.Column(
        db.String(100),
        nullable=False
    )

    capacity_liters = db.Column(
        db.Integer,
        default=100
    )

    current_fill_level = db.Column(
        db.Integer,
        default=0
    )

    waste_type = db.Column(
        db.Enum(
            "General",
            "Recyclable",
            "Organic",
            "Hazardous",
            name="waste_type"
        ),
        default="General"
    )

    status = db.Column(
        db.Enum(
            "Empty",
            "Half",
            "Full",
            "Overflowing",
            name="bin_status"
        ),
        default="Empty"
    )

    last_collected_at = db.Column(
        db.DateTime,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


    collections = db.relationship(
        "Collection",
        backref="bin",
        lazy=True
    )

    complaints = db.relationship(
        "Complaint",
        backref="bin",
        lazy=True
    )

    sensor_logs = db.relationship(
        "SensorLog",
        backref="bin",
        lazy=True
    )


    def recompute_status(
        self,
        warning_threshold=70,
        full_threshold=90
    ):

        if self.current_fill_level >= 100:

            self.status = "Overflowing"

        elif self.current_fill_level >= full_threshold:

            self.status = "Full"

        elif self.current_fill_level >= warning_threshold:

            self.status = "Half"

        else:

            self.status = (
                "Empty"
                if self.current_fill_level < warning_threshold / 2
                else "Half"
            )


    def to_dict(self):

        return {

            "id": self.id,

            "bin_code": self.bin_code,

            "location": self.location,

            "latitude": self.latitude,

            "longitude": self.longitude,

            "zone": self.zone,

            "capacity_liters":
                self.capacity_liters,

            "current_fill_level":
                self.current_fill_level,

            "waste_type":
                self.waste_type,

            "status":
                self.status,

            "last_collected_at":
                self.last_collected_at.isoformat()
                if self.last_collected_at
                else None,
        }


class SensorLog(db.Model):
    """Historical fill-level readings."""

    __tablename__ = "sensor_logs"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    bin_id = db.Column(
        db.Integer,
        db.ForeignKey("bins.id"),
        nullable=False
    )

    fill_level = db.Column(
        db.Integer,
        nullable=False
    )

    recorded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


    def to_dict(self):

        return {

            "id": self.id,

            "bin_id": self.bin_id,

            "fill_level":
                self.fill_level,

            "recorded_at":
                self.recorded_at.isoformat()

        }


class Collection(db.Model):
    """A scheduled or completed pickup of a bin."""

    __tablename__ = "collections"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    bin_id = db.Column(
        db.Integer,
        db.ForeignKey("bins.id"),
        nullable=False
    )

    collector_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    scheduled_date = db.Column(
        db.DateTime,
        nullable=False
    )

    status = db.Column(
        db.Enum(
            "Pending",
            "In Progress",
            "Completed",
            "Missed",
            name="collection_status"
        ),
        default="Pending"
    )

    notes = db.Column(
        db.String(255),
        nullable=True
    )

    completed_at = db.Column(
        db.DateTime,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


    def to_dict(self):

        return {

            "id": self.id,

            "bin_id": self.bin_id,

            "bin_code":
                self.bin.bin_code
                if self.bin
                else None,

            # FIX:
            # Send bin location to collector frontend
            "location":
                self.bin.location
                if self.bin
                else None,

            # FIX:
            # Send bin GPS coordinates
            "latitude":
                self.bin.latitude
                if self.bin
                else None,

            "longitude":
                self.bin.longitude
                if self.bin
                else None,

            "zone":
                self.bin.zone
                if self.bin
                else None,

            "current_fill_level":
                self.bin.current_fill_level
                if self.bin
                else None,

            "waste_type":
                self.bin.waste_type
                if self.bin
                else None,

            "bin_status":
                self.bin.status
                if self.bin
                else None,

            "collector_id":
                self.collector_id,

            "collector_name":
                self.collector.full_name
                if self.collector
                else None,

            "scheduled_date":
                self.scheduled_date.isoformat()
                if self.scheduled_date
                else None,

            "status":
                self.status,

            "notes":
                self.notes,

            "completed_at":
                self.completed_at.isoformat()
                if self.completed_at
                else None,

        }


class Complaint(db.Model):
    """Citizen-reported issues."""

    __tablename__ = "complaints"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    bin_id = db.Column(
        db.Integer,
        db.ForeignKey("bins.id"),
        nullable=True
    )

    reason = db.Column(
        db.Text,
        nullable=False
    )

    status = db.Column(
        db.Enum(
            "Pending",
            "In Progress",
            "Resolved",
            name="complaint_status"
        ),
        default="Pending"
    )

    reported_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    resolved_at = db.Column(
        db.DateTime,
        nullable=True
    )


    def to_dict(self):

        return {

            "id": self.id,

            "user_id": self.user_id,

            "reporter_name":
                self.reporter.full_name
                if self.reporter
                else None,

            "bin_id":
                self.bin_id,

            "bin_code":
                self.bin.bin_code
                if self.bin
                else None,

            "reason":
                self.reason,

            "status":
                self.status,

            "reported_at":
                self.reported_at.isoformat()
                if self.reported_at
                else None,

            "resolved_at":
                self.resolved_at.isoformat()
                if self.resolved_at
                else None,

        }


class Notification(db.Model):

    __tablename__ = "notifications"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    title = db.Column(
        db.String(150),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    status = db.Column(
        db.Enum(
            "Read",
            "Unread",
            name="notification_status"
        ),
        default="Unread"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


    def to_dict(self):

        return {

            "id": self.id,

            "user_id": self.user_id,

            "title": self.title,

            "message": self.message,

            "status": self.status,

            "created_at":
                self.created_at.isoformat()
                if self.created_at
                else None,

        }


class LoginHistory(db.Model):

    __tablename__ = "login_history"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    login_time = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    ip_address = db.Column(
        db.String(45),
        nullable=True
    )

    user = db.relationship(
        "User",
        backref="login_history"
    )


    def to_dict(self):

        return {

            "id": self.id,

            "user_id":
                self.user_id,

            "login_time":
                self.login_time.isoformat()
                if self.login_time
                else None,

            "ip_address":
                self.ip_address,

        }


class CollectorLocation(db.Model):
    """
    Stores GPS locations sent by collectors
    while they are performing their collection route.
    """

    __tablename__ = "collector_locations"

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )

    collector_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    latitude = db.Column(
        db.Float,
        nullable=False
    )

    longitude = db.Column(
        db.Float,
        nullable=False
    )

    current_collection_id = db.Column(
        db.Integer,
        db.ForeignKey("collections.id"),
        nullable=True
    )

    is_tracking = db.Column(
        db.Boolean,
        default=False
    )

    recorded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


    collector = db.relationship(
        "User",
        backref="location_records"
    )

    collection = db.relationship(
        "Collection",
        backref="location_records"
    )


    def to_dict(self):

        return {

            "id":
                self.id,

            "collector_id":
                self.collector_id,

            "collector_name":
                self.collector.full_name
                if self.collector
                else None,

            "latitude":
                self.latitude,

            "longitude":
                self.longitude,

            "current_collection_id":
                self.current_collection_id,

            "is_tracking":
                self.is_tracking,

            "recorded_at":
                self.recorded_at.isoformat()
                if self.recorded_at
                else None,

        }