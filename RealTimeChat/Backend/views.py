import json
import time
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Q
from .db import UserProfile, ChatMessage

# In-memory dictionary to track typing indicators
# Maps (sender_username, receiver_username) -> timestamp of last typing activity
TYPING_STATUS = {}

def get_current_user(request):
    """
    Helper function to get the current logged-in user's username.
    Supports session auth, query parameter (for ease of testing), or X-Sender header.
    """
    # 1. Check session
    username = request.session.get('username')
    if username:
        return username
    
    # 2. Check header (useful for API testing/Postman)
    username = request.headers.get('X-Sender')
    if username:
        return username

    # 3. Check query param
    username = request.GET.get('sender')
    if username:
        return username
        
    return None

def update_user_activity(username):
    """Updates the last_active timestamp for the user to keep online status current."""
    if username:
        UserProfile.objects.filter(username=username).update(last_active=timezone.now())

@csrf_exempt
def register_user(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        full_name = data.get('full_name')
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        profile_image = data.get('profile_image', '')

        if not all([full_name, username, email, password]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        if UserProfile.objects.filter(username=username).exists():
            return JsonResponse({'error': 'Username already exists'}, status=400)

        if UserProfile.objects.filter(email=email).exists():
            return JsonResponse({'error': 'Email already exists'}, status=400)

        hashed_password = make_password(password)
        user = UserProfile.objects.create(
            full_name=full_name,
            username=username,
            email=email,
            password=hashed_password,
            profile_image=profile_image,
            last_active=timezone.now()
        )

        return JsonResponse({
            'message': 'User registered successfully',
            'user': {
                'user_id': user.user_id,
                'full_name': user.full_name,
                'username': user.username,
                'email': user.email,
                'profile_image': user.profile_image
            }
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def view_users(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method is allowed'}, status=405)

    current_username = get_current_user(request)
    update_user_activity(current_username)

    search_query = request.GET.get('search', '')
    users_query = UserProfile.objects.all()

    if search_query:
        users_query = users_query.filter(
            Q(full_name__icontains=search_query) | Q(username__icontains=search_query)
        )

    users_list = []
    for user in users_query:
        # Optionally exclude the logged-in user from the user list, or include them with a flag
        users_list.append({
            'user_id': user.user_id,
            'full_name': user.full_name,
            'username': user.username,
            'email': user.email,
            'profile_image': user.profile_image,
            'is_online': user.is_online()
        })

    return JsonResponse(users_list, safe=False)

@csrf_exempt
def update_user(request, id):
    if request.method != 'PUT':
        return JsonResponse({'error': 'Only PUT method is allowed'}, status=405)

    try:
        user = UserProfile.objects.get(pk=id)
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)

    current_username = get_current_user(request)
    update_user_activity(current_username)

    try:
        data = json.loads(request.body)
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'email' in data:
            # Check unique email
            new_email = data['email']
            if UserProfile.objects.filter(email=new_email).exclude(pk=id).exists():
                return JsonResponse({'error': 'Email already in use'}, status=400)
            user.email = new_email
        if 'password' in data and data['password']:
            user.password = make_password(data['password'])
        if 'profile_image' in data:
            user.profile_image = data['profile_image']

        user.save()
        return JsonResponse({
            'message': 'User updated successfully',
            'user': {
                'user_id': user.user_id,
                'full_name': user.full_name,
                'username': user.username,
                'email': user.email,
                'profile_image': user.profile_image
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def delete_user(request, id):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Only DELETE method is allowed'}, status=405)

    try:
        user = UserProfile.objects.get(pk=id)
        user.delete()
        # If deleted user is logged in, clear session
        if request.session.get('username') == user.username:
            request.session.flush()
        return JsonResponse({'message': 'User deleted successfully'})
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def login_user(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return JsonResponse({'error': 'Username and password are required'}, status=400)

        try:
            user = UserProfile.objects.get(username=username)
        except UserProfile.DoesNotExist:
            return JsonResponse({'error': 'Invalid username or password'}, status=400)

        if not check_password(password, user.password):
            return JsonResponse({'error': 'Invalid username or password'}, status=400)

        # Set session
        request.session['username'] = user.username
        user.last_active = timezone.now()
        user.save()

        return JsonResponse({
            'message': 'Login successful',
            'user': {
                'user_id': user.user_id,
                'full_name': user.full_name,
                'username': user.username,
                'email': user.email,
                'profile_image': user.profile_image
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def logout_user(request):
    if request.method not in ['POST', 'GET']:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    request.session.flush()
    return JsonResponse({'message': 'Logout successful'})

@csrf_exempt
def get_me(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method is allowed'}, status=405)

    username = get_current_user(request)
    if not username:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        user = UserProfile.objects.get(username=username)
        user.last_active = timezone.now()
        user.save()
        return JsonResponse({
            'user': {
                'user_id': user.user_id,
                'full_name': user.full_name,
                'username': user.username,
                'email': user.email,
                'profile_image': user.profile_image,
                'is_online': user.is_online()
            }
        })
    except UserProfile.DoesNotExist:
        return JsonResponse({'error': 'User session active but profile not found'}, status=404)

@csrf_exempt
def send_message(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    sender = get_current_user(request)
    if not sender:
        return JsonResponse({'error': 'Unauthorized. Please login or provide X-Sender header.'}, status=401)
    
    update_user_activity(sender)

    try:
        data = json.loads(request.body)
        receiver = data.get('receiver')
        message = data.get('message')

        if not receiver or not message:
            return JsonResponse({'error': 'Receiver and message are required'}, status=400)

        # Check if receiver exists
        if not UserProfile.objects.filter(username=receiver).exists():
            return JsonResponse({'error': f'Receiver user "{receiver}" does not exist'}, status=400)

        chat = ChatMessage.objects.create(
            sender=sender,
            receiver=receiver,
            message=message,
            sent_at=timezone.now()
        )

        # Stop typing status once message is sent
        TYPING_STATUS.pop((sender, receiver), None)

        return JsonResponse({
            'message': 'Message sent successfully',
            'chat': {
                'chat_id': chat.chat_id,
                'sender': chat.sender,
                'receiver': chat.receiver,
                'message': chat.message,
                'sent_at': chat.sent_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def view_messages(request):
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method is allowed'}, status=405)

    current_user = get_current_user(request)
    update_user_activity(current_user)

    messages = ChatMessage.objects.all().order_by('sent_at')
    messages_list = []
    for msg in messages:
        messages_list.append({
            'chat_id': msg.chat_id,
            'sender': msg.sender,
            'receiver': msg.receiver,
            'message': msg.message,
            'sent_at': msg.sent_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    return JsonResponse(messages_list, safe=False)

@csrf_exempt
def update_message(request, id):
    if request.method != 'PUT':
        return JsonResponse({'error': 'Only PUT method is allowed'}, status=405)

    try:
        chat = ChatMessage.objects.get(pk=id)
    except ChatMessage.DoesNotExist:
        return JsonResponse({'error': 'Message not found'}, status=404)

    current_user = get_current_user(request)
    if not current_user:
        return JsonResponse({'error': 'Unauthorized. Please login.'}, status=401)
    update_user_activity(current_user)

    # Security check: User can only update their own messages
    if chat.sender != current_user:
        return JsonResponse({'error': 'Unauthorized to edit this message'}, status=403)

    try:
        data = json.loads(request.body)
        new_text = data.get('message')
        if not new_text:
            return JsonResponse({'error': 'Message text cannot be empty'}, status=400)

        chat.message = new_text
        chat.save()

        return JsonResponse({
            'message': 'Message updated successfully',
            'chat': {
                'chat_id': chat.chat_id,
                'sender': chat.sender,
                'receiver': chat.receiver,
                'message': chat.message,
                'sent_at': chat.sent_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def delete_message(request, id):
    if request.method != 'DELETE':
        return JsonResponse({'error': 'Only DELETE method is allowed'}, status=405)

    try:
        chat = ChatMessage.objects.get(pk=id)
    except ChatMessage.DoesNotExist:
        return JsonResponse({'error': 'Message not found'}, status=404)

    current_user = get_current_user(request)
    if not current_user:
        return JsonResponse({'error': 'Unauthorized. Please login.'}, status=401)
    update_user_activity(current_user)

    # Security check: User can only delete their own messages
    if chat.sender != current_user:
        return JsonResponse({'error': 'Unauthorized to delete this message'}, status=403)

    try:
        chat.delete()
        return JsonResponse({'message': 'Message deleted successfully'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def get_conversations(request):
    """
    Returns all users with whom the current logged-in user has had a conversation,
    sorted by the latest message's timestamp.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method is allowed'}, status=405)

    current_user = get_current_user(request)
    if not current_user:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    update_user_activity(current_user)

    # Get all messages where current user is sender or receiver
    messages = ChatMessage.objects.filter(
        Q(sender=current_user) | Q(receiver=current_user)
    ).order_by('-sent_at')

    # Group by contact
    conversations = {}
    for msg in messages:
        contact = msg.receiver if msg.sender == current_user else msg.sender
        if contact not in conversations:
            try:
                contact_profile = UserProfile.objects.get(username=contact)
                full_name = contact_profile.full_name
                profile_image = contact_profile.profile_image
                is_online = contact_profile.is_online()
            except UserProfile.DoesNotExist:
                full_name = contact
                profile_image = ''
                is_online = False

            conversations[contact] = {
                'username': contact,
                'full_name': full_name,
                'profile_image': profile_image,
                'is_online': is_online,
                'last_message': {
                    'chat_id': msg.chat_id,
                    'sender': msg.sender,
                    'receiver': msg.receiver,
                    'message': msg.message,
                    'sent_at': msg.sent_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            }

    return JsonResponse(list(conversations.values()), safe=False)

@csrf_exempt
def get_conversation_history(request, username):
    """
    Returns the message exchange history between the current user and the specified contact.
    Also returns whether the contact is currently typing to the current user.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Only GET method is allowed'}, status=405)

    current_user = get_current_user(request)
    if not current_user:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    update_user_activity(current_user)

    # Fetch messages exchange
    messages = ChatMessage.objects.filter(
        Q(sender=current_user, receiver=username) |
        Q(sender=username, receiver=current_user)
    ).order_by('sent_at')

    messages_list = []
    for msg in messages:
        messages_list.append({
            'chat_id': msg.chat_id,
            'sender': msg.sender,
            'receiver': msg.receiver,
            'message': msg.message,
            'sent_at': msg.sent_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    # Check typing status
    # Typing is active if the target user updated typing within the last 4 seconds
    typing_time = TYPING_STATUS.get((username, current_user), 0)
    is_typing = (time.time() - typing_time) < 4.0

    return JsonResponse({
        'messages': messages_list,
        'is_typing': is_typing
    })

@csrf_exempt
def set_typing_status(request):
    """
    Post endpoint to set the typing indicator.
    Expects body: { "receiver": "username", "is_typing": bool }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method is allowed'}, status=405)

    sender = get_current_user(request)
    if not sender:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    update_user_activity(sender)

    try:
        data = json.loads(request.body)
        receiver = data.get('receiver')
        is_typing = data.get('is_typing', False)

        if not receiver:
            return JsonResponse({'error': 'Receiver is required'}, status=400)

        if is_typing:
            TYPING_STATUS[(sender, receiver)] = time.time()
        else:
            TYPING_STATUS.pop((sender, receiver), None)

        return JsonResponse({'status': 'Typing indicator updated'})
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
