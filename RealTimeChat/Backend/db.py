from django.db import models
from django.utils import timezone

class UserProfile(models.Model):
    user_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=150)
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=256)
    profile_image = models.TextField(blank=True, default='')  # Can store base64 or a url/filename
    last_active = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.username

    def is_online(self):
        # User is online if active in the last 10 seconds
        return (timezone.now() - self.last_active).total_seconds() < 10

class ChatMessage(models.Model):
    chat_id = models.AutoField(primary_key=True)
    sender = models.CharField(max_length=100)    # username of sender
    receiver = models.CharField(max_length=100)  # username of receiver
    message = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.sender} -> {self.receiver}: {self.message[:20]}"
