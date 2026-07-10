from django.contrib import admin
from .db import UserProfile, ChatMessage

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'full_name', 'email', 'last_active')
    search_fields = ('username', 'full_name', 'email')

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'sender', 'receiver', 'message', 'sent_at')
    search_fields = ('sender', 'receiver', 'message')
