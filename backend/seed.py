"""
Populates the database with demo users, bins, and a couple of complaints so
the frontend has something to display immediately after setup.

Run with:  python seed.py
"""
import random
from datetime import datetime, timedelta

from app import create_app
from models import db, User, Bin, WasteCategory, Collection, Complaint

app = create_app()

DEMO_CATEGORIES = [
    ("General Waste", "Non-recyclable household and street waste"),
    ("Recyclable", "Paper, plastic, glass, and metal"),
    ("Organic", "Food and garden waste"),
    ("Hazardous", "Batteries, e-waste, chemicals"),
]

DEMO_BINS = [
    ("BIN-A101", "Main Street & 1st Ave", "Zone A", "General"),
    ("BIN-A102", "City Park Entrance", "Zone A", "Recyclable"),
    ("BIN-B201", "Riverside Market", "Zone B", "Organic"),
    ("BIN-B202", "Bus Terminal", "Zone B", "General"),
    ("BIN-C301", "Tech Park Gate 2", "Zone C", "Recyclable"),
    ("BIN-C302", "Community Hospital", "Zone C", "Hazardous"),
]

with app.app_context():
    db.drop_all()
    db.create_all()

    for name, desc in DEMO_CATEGORIES:
        db.session.add(WasteCategory(category_name=name, description=desc))

    admin = User(full_name="System Administrator", email="admin@smartwaste.gov",
                 phone="9990000001", role="Admin", zone="HQ")
    admin.set_password("Admin@123")

    collector = User(full_name="Raj Kumar", email="raj.collector@smartwaste.gov",
                      phone="9990000002", role="Collector", zone="Zone A")
    collector.set_password("Collector@123")

    citizen = User(full_name="Asha Mehta", email="asha@example.com",
                    phone="9990000003", role="Citizen", address="12 Green Colony",
                    zone="Zone A")
    citizen.set_password("Citizen@123")

    db.session.add_all([admin, collector, citizen])
    db.session.commit()

    bins = []
    for code, location, zone, waste_type in DEMO_BINS:
        fill = random.randint(10, 95)
        b = Bin(bin_code=code, location=location, zone=zone, waste_type=waste_type,
                current_fill_level=fill, capacity_liters=120)
        b.recompute_status()
        db.session.add(b)
        bins.append(b)
    db.session.commit()

    # A couple of scheduled collections and a sample complaint
    db.session.add(Collection(bin_id=bins[0].id, collector_id=collector.id,
                               scheduled_date=datetime.utcnow() + timedelta(hours=4),
                               notes="Routine pickup"))
    db.session.add(Complaint(user_id=citizen.id, bin_id=bins[1].id,
                              reason="Bin has been overflowing for two days near the park entrance."))
    db.session.commit()

    print("Database seeded successfully.")
    print("  Admin login:     admin@smartwaste.gov / Admin@123")
    print("  Collector login: raj.collector@smartwaste.gov / Collector@123")
    print("  Citizen login:   asha@example.com / Citizen@123")
