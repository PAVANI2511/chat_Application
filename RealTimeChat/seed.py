import os
import django
from django.utils import timezone
from datetime import datetime

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend.settings')
django.setup()

from Backend.db import UserProfile, ChatMessage
from django.contrib.auth.hashers import make_password

def seed_database():
    print("Seeding database...")
    
    # Clear existing data to make it clean
    UserProfile.objects.all().delete()
    ChatMessage.objects.all().delete()
    
    # Create rahul
    rahul = UserProfile.objects.create(
        user_id=101,
        full_name="Rahul Sharma",
        username="rahul",
        email="rahul@gmail.com",
        password=make_password("rahul123"),
        profile_image="avatar1", # avatar presets we'll define
        last_active=timezone.now()
    )
    print(f"Created user: {rahul.username}")

    # Create sneha
    sneha = UserProfile.objects.create(
        user_id=102,
        full_name="Sneha Patel",
        username="sneha",
        email="sneha@gmail.com",
        password=make_password("sneha123"),
        profile_image="avatar2",
        last_active=timezone.now()
    )
    print(f"Created user: {sneha.username}")

    # Create other mock users to populate user list and test search
    users_data = [
        ("Amit Kumar", "amit", "amit@gmail.com", "avatar3"),
        ("Priya Singh", "priya", "priya@gmail.com", "avatar4"),
        ("Vikram Malhotra", "vikram", "vikram@gmail.com", "avatar5"),
        ("Neha Gupta", "neha", "neha@gmail.com", "avatar6"),
    ]
    for fn, un, em, img in users_data:
        u = UserProfile.objects.create(
            full_name=fn,
            username=un,
            email=em,
            password=make_password("password123"),
            profile_image=img,
            last_active=timezone.now()
        )
        print(f"Created user: {u.username}")

    # Create sample message
    # "2026-07-10 10:30:00"
    sent_dt = datetime.strptime("2026-07-10 10:30:00", "%Y-%m-%d %H:%M:%S")
    # Make timezone aware
    sent_dt = timezone.make_aware(sent_dt, timezone.get_current_timezone())
    
    msg = ChatMessage.objects.create(
        chat_id=1,
        sender="rahul",
        receiver="sneha",
        message="Hello Sneha!",
        sent_at=sent_dt
    )
    print(f"Created message: {msg.sender} -> {msg.receiver}: {msg.message}")
    
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    seed_database()
