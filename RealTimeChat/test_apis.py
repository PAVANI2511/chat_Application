import requests
import json
import sys

API_BASE = "http://127.0.0.1:8000"

def run_tests():
    print("Starting API Integration Tests...\n")
    session1 = requests.Session()
    session2 = requests.Session()

    # 1. Test User Registration
    print("Test 1: User Registration...")
    reg_data_1 = {
        "full_name": "Test User One",
        "username": "testuser1",
        "email": "testuser1@example.com",
        "password": "testpassword123",
        "profile_image": "avatar1"
    }
    res = requests.post(f"{API_BASE}/users/register/", json=reg_data_1)
    print(f"Status: {res.status_code}")
    assert res.status_code == 201, f"Expected 201, got {res.status_code}. Response: {res.text}"
    user1_data = res.json()["user"]
    user1_id = user1_data["user_id"]
    print(f"Registered User 1 successfully. ID: {user1_id}\n")

    reg_data_2 = {
        "full_name": "Test User Two",
        "username": "testuser2",
        "email": "testuser2@example.com",
        "password": "testpassword123",
        "profile_image": "avatar2"
    }
    res = requests.post(f"{API_BASE}/users/register/", json=reg_data_2)
    print(f"Status: {res.status_code}")
    assert res.status_code == 201, f"Expected 201, got {res.status_code}. Response: {res.text}"
    user2_data = res.json()["user"]
    user2_id = user2_data["user_id"]
    print(f"Registered User 2 successfully. ID: {user2_id}\n")

    # 2. Test User Login
    print("Test 2: User Login...")
    login_data_1 = {
        "username": "testuser1",
        "password": "testpassword123"
    }
    res = session1.post(f"{API_BASE}/users/login/", json=login_data_1)
    print(f"Status: {res.status_code}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}. Response: {res.text}"
    print("Logged in as User 1 successfully.\n")

    login_data_2 = {
        "username": "testuser2",
        "password": "testpassword123"
    }
    res = session2.post(f"{API_BASE}/users/login/", json=login_data_2)
    print(f"Status: {res.status_code}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}. Response: {res.text}"
    print("Logged in as User 2 successfully.\n")

    # 3. Test View All Users
    print("Test 3: View All Users...")
    res = session1.get(f"{API_BASE}/users/")
    print(f"Status: {res.status_code}")
    assert res.status_code == 200
    users = res.json()
    print(f"Total registered users returned: {len(users)}")
    usernames = [u["username"] for u in users]
    assert "testuser1" in usernames
    assert "testuser2" in usernames
    print("View all users test passed.\n")

    # 4. Test Search Users
    print("Test 4: Search Users...")
    res = session1.get(f"{API_BASE}/users/?search=testuser")
    print(f"Status: {res.status_code}")
    assert res.status_code == 200
    users_search = res.json()
    print(f"Search results for 'testuser': {len(users_search)}")
    for u in users_search:
        assert "testuser" in u["username"]
    print("Search users test passed.\n")

    # 5. Test Send Messages
    print("Test 5: Send Messages...")
    # Send message from user1 to user2
    msg_data = {
        "receiver": "testuser2",
        "message": "Hello testuser2, this is a test message!"
    }
    res = session1.post(f"{API_BASE}/chats/send/", json=msg_data)
    print(f"Status: {res.status_code}")
    assert res.status_code == 201, f"Expected 201, got {res.status_code}. Response: {res.text}"
    chat_data = res.json()["chat"]
    chat_id = chat_data["chat_id"]
    print(f"Sent message successfully. Chat ID: {chat_id}\n")

    # 6. Test View All Messages
    print("Test 6: View All Messages...")
    res = session1.get(f"{API_BASE}/chats/")
    print(f"Status: {res.status_code}")
    assert res.status_code == 200
    all_msgs = res.json()
    print(f"Total messages in system: {len(all_msgs)}")
    print("View all messages test passed.\n")

    # 7. Test Conversation List (History summary)
    print("Test 7: Conversation Summary List...")
    res = session1.get(f"{API_BASE}/conversation/")
    print(f"Status: {res.status_code}")
    assert res.status_code == 200
    convs = res.json()
    print(f"Conversations list for user 1: {json.dumps(convs, indent=2)}")
    assert len(convs) >= 1
    assert convs[0]["username"] == "testuser2"
    print("Conversation summary test passed.\n")

    # 8. Test Conversation History Detail
    print("Test 8: Conversation History Detail...")
    res = session1.get(f"{API_BASE}/conversation/testuser2/")
    print(f"Status: {res.status_code}")
    assert res.status_code == 200
    history = res.json()
    print(f"History messages count: {len(history['messages'])}")
    assert len(history['messages']) == 1
    assert history['messages'][0]['message'] == "Hello testuser2, this is a test message!"
    print("Conversation history detail test passed.\n")

    # 9. Test Update Message (Edit)
    print("Test 9: Update Message...")
    update_data = {
        "message": "Hello testuser2, this is an EDITED test message!"
    }
    res = session1.put(f"{API_BASE}/chats/update/{chat_id}/", json=update_data)
    print(f"Status: {res.status_code}")
    assert res.status_code == 200
    updated_chat = res.json()["chat"]
    assert updated_chat["message"] == "Hello testuser2, this is an EDITED test message!"
    print("Update message test passed.\n")

    # 10. Test Update User Profile
    print("Test 10: Update User Profile...")
    update_user_data = {
        "full_name": "Test User One Updated",
        "email": "testuser1_new@example.com"
    }
    res = session1.put(f"{API_BASE}/users/update/{user1_id}/", json=update_user_data)
    print(f"Status: {res.status_code}")
    assert res.status_code == 200
    updated_user = res.json()["user"]
    assert updated_user["full_name"] == "Test User One Updated"
    assert updated_user["email"] == "testuser1_new@example.com"
    print("Update user profile test passed.\n")

    # 11. Test Delete Message
    print("Test 11: Delete Message...")
    res = session1.delete(f"{API_BASE}/chats/delete/{chat_id}/")
    print(f"Status: {res.status_code}")
    assert res.status_code == 200
    
    # Confirm deletion from history
    res = session1.get(f"{API_BASE}/conversation/testuser2/")
    assert len(res.json()["messages"]) == 0
    print("Delete message test passed.\n")

    # 12. Test Delete User
    print("Test 12: Delete User...")
    res = session1.delete(f"{API_BASE}/users/delete/{user1_id}/")
    print(f"Status: {res.status_code}")
    assert res.status_code == 200
    
    # Confirm deletion from users list
    res = session2.get(f"{API_BASE}/users/")
    users = res.json()
    usernames = [u["username"] for u in users]
    assert "testuser1" not in usernames
    print("Delete user test passed.\n")

    print("ALL REST API INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    try:
        run_tests()
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        sys.exit(1)
