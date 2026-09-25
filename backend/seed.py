"""
Adds the required demo users for the Smart Waste Management System.

This script is SAFE to run multiple times.
Existing users and existing project data are not deleted or modified.

Run with:
    python seed.py
"""

from app import create_app
from models import db, User


app = create_app()


USERS = [
    # =========================================================
    # ADMIN
    # =========================================================
    {
        "full_name": "Sasmit Malhotra",
        "email": "sasmitmalhotra@gmail.com",
        "phone": "6358857660",
        "password": "25102005",
        "zone": "A",
        "role": "Admin",
    },

    # =========================================================
    # ZONE A
    # =========================================================
    {
        "full_name": "Aarav",
        "email": "aaravpatel@gmail.com",
        "phone": "7879065430",
        "password": "0010",
        "zone": "A",
        "role": "Citizen",
    },
    {
        "full_name": "Diya",
        "email": "diyashah@gmail.com",
        "phone": "8768906540",
        "password": "0090",
        "zone": "A",
        "role": "Citizen",
    },
    {
        "full_name": "Amit",
        "email": "amit123@gmail.com",
        "phone": "9876543211",
        "password": "1234",
        "zone": "A",
        "role": "Collector",
    },
    {
        "full_name": "Riya",
        "email": "riya123@gmail.com",
        "phone": "9876543212",
        "password": "1234",
        "zone": "A",
        "role": "Citizen",
    },

    # =========================================================
    # ZONE B
    # =========================================================
    {
        "full_name": "John Doe",
        "email": "you@gmail.com",
        "phone": "9897648282",
        "password": "12345",
        "zone": "B",
        "role": "Collector",
    },
    {
        "full_name": "Vivaan",
        "email": "vivaandesai@gmail.com",
        "phone": "9090102340",
        "password": "0030",
        "zone": "B",
        "role": "Citizen",
    },
    {
        "full_name": "Dev",
        "email": "dev123@gmail.com",
        "phone": "9876543213",
        "password": "1234",
        "zone": "B",
        "role": "Collector",
    },
    {
        "full_name": "Neha",
        "email": "neha123@gmail.com",
        "phone": "9876543214",
        "password": "1234",
        "zone": "B",
        "role": "Citizen",
    },
    {
        "full_name": "Raj",
        "email": "raj123@gmail.com",
        "phone": "9876543215",
        "password": "1234",
        "zone": "B",
        "role": "Citizen",
    },

    # =========================================================
    # ZONE C
    # =========================================================
    {
        "full_name": "Hari Prasad",
        "email": "you1234@gmail.com",
        "phone": "9245640000",
        "password": "123456",
        "zone": "C",
        "role": "Citizen",
    },
    {
        "full_name": "Rahul",
        "email": "rahul1234@gmail.com",
        "phone": "424345690",
        "password": "25102005",
        "zone": "C",
        "role": "Collector",
    },
    {
        "full_name": "Jay",
        "email": "jay123@gmail.com",
        "phone": "9876543216",
        "password": "1234",
        "zone": "C",
        "role": "Collector",
    },
    {
        "full_name": "Mia",
        "email": "mia123@gmail.com",
        "phone": "9876543217",
        "password": "1234",
        "zone": "C",
        "role": "Citizen",
    },
    {
        "full_name": "Dev",
        "email": "dev456@gmail.com",
        "phone": "9876543218",
        "password": "1234",
        "zone": "C",
        "role": "Citizen",
    },

    # =========================================================
    # ZONE D
    # =========================================================
    {
        "full_name": "Karan",
        "email": "karan123@gmail.com",
        "phone": "5456789300",
        "password": "12367",
        "zone": "D",
        "role": "Collector",
    },
    {
        "full_name": "Karan",
        "email": "karan456@gmail.com",
        "phone": "9876543219",
        "password": "1234",
        "zone": "D",
        "role": "Collector",
    },
    {
        "full_name": "Ananya",
        "email": "ananya123@gmail.com",
        "phone": "9876543220",
        "password": "1234",
        "zone": "D",
        "role": "Citizen",
    },
    {
        "full_name": "Siya",
        "email": "siya123@gmail.com",
        "phone": "9876543221",
        "password": "1234",
        "zone": "D",
        "role": "Citizen",
    },
    {
        "full_name": "Om",
        "email": "om123@gmail.com",
        "phone": "9876543222",
        "password": "1234",
        "zone": "D",
        "role": "Citizen",
    },

    # =========================================================
    # ZONE E
    # =========================================================
    {
        "full_name": "Jay",
        "email": "jay546@gmail.com",
        "phone": "6634567890",
        "password": "00987",
        "zone": "E",
        "role": "Collector",
    },
    {
        "full_name": "Arjun",
        "email": "arjun123@gmail.com",
        "phone": "9876543223",
        "password": "1234",
        "zone": "E",
        "role": "Collector",
    },
    {
        "full_name": "Anya",
        "email": "anya123@gmail.com",
        "phone": "9876543224",
        "password": "1234",
        "zone": "E",
        "role": "Citizen",
    },
    {
        "full_name": "Yash",
        "email": "yash123@gmail.com",
        "phone": "9876543225",
        "password": "1234",
        "zone": "E",
        "role": "Citizen",
    },
    {
        "full_name": "Tara",
        "email": "tara123@gmail.com",
        "phone": "9876543226",
        "password": "1234",
        "zone": "E",
        "role": "Citizen",
    },
]


def add_users():
    added = 0
    skipped = 0

    for data in USERS:
        existing_user = User.query.filter_by(
            email=data["email"]
        ).first()

        if existing_user:
            print(
                f"SKIPPED: {data['email']} "
                f"(already exists)"
            )
            skipped += 1
            continue

        user = User(
            full_name=data["full_name"],
            email=data["email"],
            phone=data["phone"],
            role=data["role"],
            zone=data["zone"],
        )

        user.set_password(data["password"])

        db.session.add(user)

        print(
            f"ADDED: {data['full_name']} | "
            f"{data['role']} | "
            f"Zone {data['zone']}"
        )

        added += 1

    db.session.commit()

    print()
    print("=" * 45)
    print("USER SEEDING COMPLETE")
    print("=" * 45)
    print(f"Users added  : {added}")
    print(f"Users skipped: {skipped}")
    print("=" * 45)


if __name__ == "__main__":
    with app.app_context():
        add_users()