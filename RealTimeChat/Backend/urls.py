from django.urls import path
from . import views

urlpatterns = [
    # User Management Endpoints
    path('users/register/', views.register_user, name='register_user'),
    path('users/', views.view_users, name='view_users'),
    path('users/update/<int:id>/', views.update_user, name='update_user'),
    path('users/delete/<int:id>/', views.delete_user, name='delete_user'),
    path('users/login/', views.login_user, name='login_user'),
    path('users/logout/', views.logout_user, name='logout_user'),
    path('users/me/', views.get_me, name='get_me'),

    # Chat Management Endpoints
    path('chats/send/', views.send_message, name='send_message'),
    path('chats/', views.view_messages, name='view_messages'),
    path('chats/update/<int:id>/', views.update_message, name='update_message'),
    path('chats/delete/<int:id>/', views.delete_message, name='delete_message'),
    path('chats/typing/', views.set_typing_status, name='set_typing_status'),

    # Conversation Management Endpoints
    path('conversation/', views.get_conversations, name='get_conversations'),
    path('conversation/<str:username>/', views.get_conversation_history, name='get_conversation_history'),
]
