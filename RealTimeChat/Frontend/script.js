// API Base URL config
const API_BASE = 'http://127.0.0.1:8000';

// Global presets mapping
const AVATAR_PRESETS = {
    'avatar1': 'https://api.dicebear.com/7.x/lorelei/svg?seed=Felix',
    'avatar2': 'https://api.dicebear.com/7.x/lorelei/svg?seed=Aneka',
    'avatar3': 'https://api.dicebear.com/7.x/lorelei/svg?seed=Jack',
    'avatar4': 'https://api.dicebear.com/7.x/lorelei/svg?seed=Sasha',
    'avatar5': 'https://api.dicebear.com/7.x/lorelei/svg?seed=George',
    'avatar6': 'https://api.dicebear.com/7.x/lorelei/svg?seed=Molly',
};

// Helper: Resolve avatar image source
function getAvatarUrl(avatarStr) {
    if (!avatarStr) {
        return 'https://api.dicebear.com/7.x/lorelei/svg?seed=placeholder';
    }
    if (avatarStr.startsWith('data:image/') || avatarStr.startsWith('http')) {
        return avatarStr;
    }
    return AVATAR_PRESETS[avatarStr] || AVATAR_PRESETS['avatar1'];
}

// Helper: Show custom toast notification
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    // Remove toast after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'fadeIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Fetch helper with default headers and credentials
async function customFetch(endpoint, options = {}) {
    const userJson = localStorage.getItem('currentUser');
    const currentUser = userJson ? JSON.parse(userJson) : null;
    
    // Prepare default headers
    const headers = {
        'Content-Type': 'application/json',
        ...(options.headers || {})
    };

    // If logged in, add X-Sender fallback header to support local filesystem fetches
    if (currentUser && currentUser.username) {
        headers['X-Sender'] = currentUser.username;
    }

    const config = {
        credentials: 'include', // send session cookies if supported by origin
        ...options,
        headers: headers
    };

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, config);
        
        // Handle unauthorized redirections
        if (response.status === 401 && !endpoint.includes('/users/login') && !endpoint.includes('/users/register')) {
            localStorage.removeItem('currentUser');
            if (window.location.pathname.includes('dashboard.html')) {
                window.location.href = 'login.html';
            }
        }
        
        return response;
    } catch (err) {
        console.error("Fetch network error:", err);
        showToast("Server connection error. Is the backend running?", "error");
        throw err;
    }
}

/* ========================================= */
/* PAGE: REGISTRATION                        */
/* ========================================= */
if (document.getElementById('register-form')) {
    const form = document.getElementById('register-form');
    const avatarPicker = document.getElementById('avatar-picker');
    const customAvatarInput = document.getElementById('custom-avatar');
    const uploadStatus = document.getElementById('file-upload-status');
    let selectedAvatar = 'avatar1'; // Default

    // Preset selection handler
    avatarPicker.querySelectorAll('.avatar-option').forEach(option => {
        option.addEventListener('click', () => {
            avatarPicker.querySelectorAll('.avatar-option').forEach(o => o.classList.remove('selected'));
            option.classList.add('selected');
            selectedAvatar = option.getAttribute('data-avatar');
            uploadStatus.textContent = ""; // Clear file upload status
        });
    });

    // Custom image upload handler (reads as Base64)
    customAvatarInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            if (file.size > 2 * 1024 * 1024) { // Limit to 2MB
                showToast("File size too large. Max 2MB.", "error");
                customAvatarInput.value = "";
                return;
            }
            const reader = new FileReader();
            reader.onload = (event) => {
                selectedAvatar = event.target.result; // Base64 encoding
                avatarPicker.querySelectorAll('.avatar-option').forEach(o => o.classList.remove('selected'));
                uploadStatus.textContent = `Custom image uploaded! (${file.name})`;
                showToast("Custom profile image loaded.");
            };
            reader.readAsDataURL(file);
        }
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const fullName = document.getElementById('full-name').value.trim();
        const username = document.getElementById('username').value.trim();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;

        try {
            const res = await customFetch('/users/register/', {
                method: 'POST',
                body: JSON.stringify({
                    full_name: fullName,
                    username: username,
                    email: email,
                    password: password,
                    profile_image: selectedAvatar
                })
            });

            const data = await res.json();
            if (res.ok) {
                showToast("Registration successful! Redirecting to login...", "success");
                setTimeout(() => {
                    window.location.href = 'login.html';
                }, 1500);
            } else {
                showToast(data.error || "Registration failed.", "error");
            }
        } catch (err) {
            console.error("Reg error:", err);
        }
    });
}

/* ========================================= */
/* PAGE: LOGIN                               */
/* ========================================= */
if (document.getElementById('login-form')) {
    const form = document.getElementById('login-form');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;

        try {
            const res = await customFetch('/users/login/', {
                method: 'POST',
                body: JSON.stringify({ username, password })
            });

            const data = await res.json();
            if (res.ok) {
                // Save user details to localStorage
                localStorage.setItem('currentUser', JSON.stringify(data.user));
                showToast("Login successful! Redirecting...", "success");
                setTimeout(() => {
                    window.location.href = 'dashboard.html';
                }, 1500);
            } else {
                showToast(data.error || "Invalid username or password.", "error");
            }
        } catch (err) {
            console.error("Login error:", err);
        }
    });
}

/* ========================================= */
/* PAGE: DASHBOARD                           */
/* ========================================= */
if (window.location.pathname.includes('dashboard.html') || document.getElementById('active-chat-container')) {
    let currentUser = null;
    let selectedContact = null; // Holds the full contact profile object
    let activeTab = 'chats';    // 'chats' (Recent Chats) or 'users' (All Users)
    let chatInterval = null;    // Timer for refreshing messages
    let sidebarInterval = null; // Timer for refreshing status and lists
    let typingTimeout = null;   // Typing status timeout
    let lastTypingSent = 0;     // Timestamp of last sent typing flag

    // Check auth
    function checkAuthentication() {
        const cachedUser = localStorage.getItem('currentUser');
        if (!cachedUser) {
            window.location.href = 'login.html';
            return;
        }
        currentUser = JSON.parse(cachedUser);
        
        // Fetch fresh details from backend to confirm session
        customFetch('/users/me/').then(async res => {
            if (res.ok) {
                const data = await res.json();
                currentUser = data.user;
                localStorage.setItem('currentUser', JSON.stringify(currentUser));
                displayCurrentUser();
            } else {
                localStorage.removeItem('currentUser');
                window.location.href = 'login.html';
            }
        }).catch(() => {
            // Keep local cached user if offline temporarily
            displayCurrentUser();
        });
    }

    // Display Current Logged In User
    function displayCurrentUser() {
        if (!currentUser) return;
        document.getElementById('current-user-name').textContent = currentUser.full_name;
        document.getElementById('current-user-username').textContent = `@${currentUser.username}`;
        document.getElementById('current-user-avatar').src = getAvatarUrl(currentUser.profile_image);
    }

    // Tab toggles
    const tabChats = document.getElementById('tab-chats');
    const tabUsers = document.getElementById('tab-users');

    tabChats.addEventListener('click', () => {
        activeTab = 'chats';
        tabChats.style.color = 'var(--accent-color)';
        tabChats.style.borderBottom = '2px solid var(--accent-color)';
        tabUsers.style.color = 'var(--text-secondary)';
        tabUsers.style.borderBottom = 'none';
        loadSidebarList();
    });

    tabUsers.addEventListener('click', () => {
        activeTab = 'users';
        tabUsers.style.color = 'var(--accent-color)';
        tabUsers.style.borderBottom = '2px solid var(--accent-color)';
        tabChats.style.color = 'var(--text-secondary)';
        tabChats.style.borderBottom = 'none';
        loadSidebarList();
    });

    // Load list of Chats or Users
    async function loadSidebarList() {
        const container = document.getElementById('users-list-container');
        const searchQuery = document.getElementById('user-search').value.trim();

        try {
            let endpoint = activeTab === 'chats' ? '/conversation/' : '/users/';
            if (searchQuery) {
                endpoint = `/users/?search=${encodeURIComponent(searchQuery)}`;
            }

            const res = await customFetch(endpoint);
            if (!res.ok) return;

            const data = await res.json();
            container.innerHTML = "";

            if (data.length === 0) {
                container.innerHTML = `<div style="text-align:center; padding:30px; color:var(--text-muted);">No ${activeTab} found.</div>`;
                return;
            }

            data.forEach(item => {
                // If it is 'All Users' view, exclude current user
                if (activeTab === 'users' && item.username === currentUser.username) {
                    return;
                }

                const userItem = document.createElement('div');
                userItem.className = `user-item ${selectedContact && selectedContact.username === item.username ? 'active' : ''}`;
                
                let lastMsgHtml = "";
                let timeHtml = "";
                
                if (activeTab === 'chats' && item.last_message) {
                    lastMsgHtml = `<div class="user-item-lastmsg">${item.last_message.sender === currentUser.username ? 'You: ' : ''}${item.last_message.message}</div>`;
                    
                    // Format timestamp
                    try {
                        const date = new Date(item.last_message.sent_at);
                        timeHtml = `<span class="user-item-time">${date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>`;
                    } catch (e) {
                        timeHtml = "";
                    }
                } else {
                    lastMsgHtml = `<div class="user-item-lastmsg">@${item.username}</div>`;
                }

                userItem.innerHTML = `
                    <div class="avatar-wrapper">
                        <img class="user-avatar" src="${getAvatarUrl(item.profile_image)}" alt="Avatar">
                        <span class="status-badge ${item.is_online ? 'online' : 'offline'}"></span>
                    </div>
                    <div class="user-item-details">
                        <div class="user-item-header">
                            <span class="user-item-name">${item.full_name}</span>
                            ${timeHtml}
                        </div>
                        ${lastMsgHtml}
                    </div>
                `;

                userItem.addEventListener('click', () => {
                    selectContact(item);
                });

                container.appendChild(userItem);
            });

        } catch (err) {
            console.error("Load sidebar list error:", err);
        }
    }

    // Search Box Listener
    document.getElementById('user-search').addEventListener('input', () => {
        loadSidebarList();
    });

    // Select active chat user
    function selectContact(contact) {
        selectedContact = contact;
        
        // Hide placeholder, show chat screen
        document.getElementById('chat-placeholder').style.display = 'none';
        document.getElementById('active-chat-container').style.display = 'flex';

        // Update Chat Header
        document.getElementById('active-chat-avatar').src = getAvatarUrl(contact.profile_image);
        document.getElementById('active-chat-name').textContent = contact.full_name;
        updateContactStatusDisplay(contact.is_online);

        // Highlight selected item in sidebar list
        document.querySelectorAll('.user-item').forEach(el => {
            const nameEl = el.querySelector('.user-item-name');
            if (nameEl && nameEl.textContent === contact.full_name) {
                el.classList.add('active');
            } else {
                el.classList.remove('active');
            }
        });

        // Mobile responsiveness: Show chat pane and hide sidebar
        if (window.innerWidth <= 768) {
            document.getElementById('sidebar').classList.add('hidden');
            document.getElementById('chat-pane').classList.remove('hidden');
        }

        // Fetch messages
        fetchChatHistory(true);

        // Clear and restart polling intervals
        if (chatInterval) clearInterval(chatInterval);
        chatInterval = setInterval(() => fetchChatHistory(false), 3000);
    }

    function updateContactStatusDisplay(isOnline) {
        const badge = document.getElementById('active-chat-status-badge');
        const text = document.getElementById('active-chat-status');
        
        badge.className = `status-badge ${isOnline ? 'online' : 'offline'}`;
        text.textContent = isOnline ? 'Online' : 'Offline';
        text.className = `active-chat-status ${isOnline ? 'online' : ''}`;
    }

    // Back to sidebar button on mobile view
    const backBtn = document.getElementById('back-to-list');
    backBtn.addEventListener('click', () => {
        document.getElementById('sidebar').classList.remove('hidden');
        document.getElementById('chat-pane').classList.add('hidden');
        if (chatInterval) {
            clearInterval(chatInterval);
            chatInterval = null;
        }
    });

    // Fetch message history with selected contact
    let lastMessageCount = 0;
    async function fetchChatHistory(forceScroll = false) {
        if (!selectedContact) return;

        try {
            const res = await customFetch(`/conversation/${selectedContact.username}/`);
            if (!res.ok) return;

            const data = await res.json();
            const messages = data.messages;
            const isTyping = data.is_typing;

            // Render Messages
            const container = document.getElementById('chat-messages-container');
            container.innerHTML = "";

            if (messages.length === 0) {
                container.innerHTML = `<div style="text-align: center; padding: 40px; color: var(--text-muted);">No messages yet. Send a hello!</div>`;
                lastMessageCount = 0;
            } else {
                messages.forEach(msg => {
                    const isSent = msg.sender === currentUser.username;
                    const wrapper = document.createElement('div');
                    wrapper.className = `message-wrapper ${isSent ? 'sent' : 'received'}`;
                    wrapper.id = `msg-${msg.chat_id}`;

                    // Extract date format
                    let displayTime = "";
                    try {
                        const date = new Date(msg.sent_at);
                        displayTime = date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                    } catch (e) {
                        displayTime = msg.sent_at;
                    }

                    // Render avatar for received message
                    const avatarHtml = isSent ? "" : `<img class="msg-avatar" src="${getAvatarUrl(selectedContact.profile_image)}" alt="Avatar">`;

                    // Actions menu for sent messages
                    const actionsHtml = isSent ? `
                        <div class="message-actions-menu">
                            <button class="action-menu-btn" onclick="initiateEditMessage(${msg.chat_id}, '${escapeHtml(msg.message)}')" title="Edit"><i class="fa-solid fa-pen"></i></button>
                            <button class="action-menu-btn delete" onclick="deleteMessage(${msg.chat_id})" title="Delete"><i class="fa-solid fa-trash"></i></button>
                        </div>
                    ` : "";

                    wrapper.innerHTML = `
                        ${avatarHtml}
                        <div class="message-bubble-container">
                            <div class="message-bubble">
                                <span class="message-text">${escapeHtml(msg.message)}</span>
                            </div>
                            <span class="message-time">${displayTime}</span>
                        </div>
                        ${actionsHtml}
                    `;

                    container.appendChild(wrapper);
                });
            }

            // Show typing indicator
            const typingIndicator = document.getElementById('typing-indicator');
            const typingUsername = document.getElementById('typing-username');
            if (isTyping) {
                typingUsername.textContent = selectedContact.full_name;
                typingIndicator.style.display = 'block';
            } else {
                typingIndicator.style.display = 'none';
            }

            // Scroll to bottom if message count increased or forced
            if (forceScroll || messages.length > lastMessageCount) {
                container.scrollTop = container.scrollHeight;
            }
            lastMessageCount = messages.length;

        } catch (err) {
            console.error("History fetch error:", err);
        }
    }

    // Escape HTML helper
    function escapeHtml(unsafe) {
        return unsafe
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
    }

    // Sending Message
    const sendForm = document.getElementById('chat-send-form');
    const msgInput = document.getElementById('chat-message-input');

    sendForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = msgInput.value.trim();
        if (!text || !selectedContact) return;

        try {
            const res = await customFetch('/chats/send/', {
                method: 'POST',
                body: JSON.stringify({
                    receiver: selectedContact.username,
                    message: text
                })
            });

            if (res.ok) {
                msgInput.value = "";
                // Report finished typing
                sendTypingStatus(false);
                fetchChatHistory(true);
            } else {
                const data = await res.json();
                showToast(data.error || "Failed to send message", "error");
            }
        } catch (err) {
            console.error("Send message error:", err);
        }
    });

    // Typing status sender logic
    msgInput.addEventListener('input', () => {
        if (!selectedContact) return;

        const now = Date.now();
        if (now - lastTypingSent > 2000) { // send every 2 seconds
            sendTypingStatus(true);
            lastTypingSent = now;
        }

        // Reset inactivity timer
        clearTimeout(typingTimeout);
        typingTimeout = setTimeout(() => {
            sendTypingStatus(false);
        }, 3000); // Stop typing status after 3 seconds of inactivity
    });

    async function sendTypingStatus(isTyping) {
        if (!selectedContact) return;
        try {
            await customFetch('/chats/typing/', {
                method: 'POST',
                body: JSON.stringify({
                    receiver: selectedContact.username,
                    is_typing: isTyping
                })
            });
        } catch(e) {
            // Silently absorb typing status updates failures
        }
    }

    // Emoji Picker Trigger
    const emojiBtn = document.getElementById('emoji-btn');
    const emojiPicker = document.getElementById('emoji-picker');

    emojiBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        emojiPicker.style.display = emojiPicker.style.display === 'grid' ? 'none' : 'grid';
    });

    // Insert emoji on click
    emojiPicker.querySelectorAll('.emoji-option').forEach(emoji => {
        emoji.addEventListener('click', () => {
            msgInput.value += emoji.textContent;
            emojiPicker.style.display = 'none';
            msgInput.focus();
        });
    });

    // Close emoji picker when clicking elsewhere
    document.addEventListener('click', () => {
        emojiPicker.style.display = 'none';
    });

    /* --- Inline Edit & Delete Operations --- */
    window.initiateEditMessage = function(chatId, currentMsg) {
        const msgWrapper = document.getElementById(`msg-${chatId}`);
        if (!msgWrapper) return;

        const bubble = msgWrapper.querySelector('.message-bubble');
        const originalContent = bubble.innerHTML;

        bubble.innerHTML = `
            <div class="edit-input-wrapper">
                <input type="text" class="edit-textbox" value="${escapeHtml(currentMsg)}" id="edit-input-${chatId}">
                <div class="edit-actions">
                    <button class="edit-btn btn-secondary" onclick="cancelEditMessage(${chatId}, '${escapeHtml(currentMsg)}')">Cancel</button>
                    <button class="edit-btn btn-primary" onclick="saveEditMessage(${chatId})">Save</button>
                </div>
            </div>
        `;
        
        // Hide actions menu while editing
        const actionsMenu = msgWrapper.querySelector('.message-actions-menu');
        if (actionsMenu) actionsMenu.style.display = 'none';
    };

    window.cancelEditMessage = function(chatId, originalText) {
        const msgWrapper = document.getElementById(`msg-${chatId}`);
        if (!msgWrapper) return;
        
        const bubble = msgWrapper.querySelector('.message-bubble');
        bubble.innerHTML = `<span class="message-text">${escapeHtml(originalText)}</span>`;

        const actionsMenu = msgWrapper.querySelector('.message-actions-menu');
        if (actionsMenu) actionsMenu.style.display = 'flex';
    };

    window.saveEditMessage = async function(chatId) {
        const input = document.getElementById(`edit-input-${chatId}`);
        if (!input) return;

        const text = input.value.trim();
        if (!text) {
            showToast("Message cannot be empty", "error");
            return;
        }

        try {
            const res = await customFetch(`/chats/update/${chatId}/`, {
                method: 'PUT',
                body: JSON.stringify({ message: text })
            });

            if (res.ok) {
                showToast("Message updated successfully!");
                fetchChatHistory(false);
            } else {
                const data = await res.json();
                showToast(data.error || "Update failed", "error");
            }
        } catch (err) {
            console.error("Edit message error:", err);
        }
    };

    window.deleteMessage = async function(chatId) {
        if (!confirm("Are you sure you want to delete this message?")) return;

        try {
            const res = await customFetch(`/chats/delete/${chatId}/`, {
                method: 'DELETE'
            });

            if (res.ok) {
                showToast("Message deleted");
                fetchChatHistory(false);
            } else {
                const data = await res.json();
                showToast(data.error || "Deletion failed", "error");
            }
        } catch (err) {
            console.error("Delete message error:", err);
        }
    };

    /* --- Profile Settings Dialog --- */
    const profileModal = document.getElementById('profile-modal');
    const profileBtn = document.getElementById('profile-settings-btn');
    const profileClose = document.getElementById('profile-modal-close');
    const profileForm = document.getElementById('profile-update-form');
    const profileAvatarPicker = document.getElementById('profile-avatar-picker');
    const profilePreview = document.getElementById('profile-edit-preview');
    const profileCustomInput = document.getElementById('profile-custom-avatar');
    let profileSelectedAvatar = '';

    profileBtn.addEventListener('click', () => {
        if (!currentUser) return;
        
        // Populate fields
        document.getElementById('profile-full-name').value = currentUser.full_name;
        document.getElementById('profile-email').value = currentUser.email;
        document.getElementById('profile-password').value = ""; // Always blank initially
        
        profileSelectedAvatar = currentUser.profile_image;
        profilePreview.src = getAvatarUrl(profileSelectedAvatar);

        // Highlight preset if it matches
        profileAvatarPicker.querySelectorAll('.avatar-option').forEach(opt => {
            if (opt.getAttribute('data-avatar') === profileSelectedAvatar) {
                opt.classList.add('selected');
            } else {
                opt.classList.remove('selected');
            }
        });

        profileModal.style.display = 'flex';
    });

    profileClose.addEventListener('click', () => {
        profileModal.style.display = 'none';
    });

    // Preset selection handler inside profile modal
    profileAvatarPicker.querySelectorAll('.avatar-option').forEach(option => {
        option.addEventListener('click', () => {
            profileAvatarPicker.querySelectorAll('.avatar-option').forEach(o => o.classList.remove('selected'));
            option.classList.add('selected');
            profileSelectedAvatar = option.getAttribute('data-avatar');
            profilePreview.src = getAvatarUrl(profileSelectedAvatar);
        });
    });

    // Custom image upload inside profile modal
    profileCustomInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            if (file.size > 2 * 1024 * 1024) {
                showToast("File size too large. Max 2MB.", "error");
                profileCustomInput.value = "";
                return;
            }
            const reader = new FileReader();
            reader.onload = (event) => {
                profileSelectedAvatar = event.target.result;
                profileAvatarPicker.querySelectorAll('.avatar-option').forEach(o => o.classList.remove('selected'));
                profilePreview.src = profileSelectedAvatar;
                showToast("Custom preview loaded.");
            };
            reader.readAsDataURL(file);
        }
    });

    // Submit Profile Updates
    profileForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fullName = document.getElementById('profile-full-name').value.trim();
        const email = document.getElementById('profile-email').value.trim();
        const password = document.getElementById('profile-password').value;

        const body = {
            full_name: fullName,
            email: email,
            profile_image: profileSelectedAvatar
        };

        if (password) {
            body.password = password;
        }

        try {
            const res = await customFetch(`/users/update/${currentUser.user_id}/`, {
                method: 'PUT',
                body: JSON.stringify(body)
            });

            const data = await res.json();
            if (res.ok) {
                showToast("Profile updated successfully!");
                currentUser = data.user;
                localStorage.setItem('currentUser', JSON.stringify(currentUser));
                displayCurrentUser();
                profileModal.style.display = 'none';
                
                // If chatting, reload messages to update avatars
                if (selectedContact) {
                    fetchChatHistory(false);
                }
            } else {
                showToast(data.error || "Update failed", "error");
            }
        } catch (err) {
            console.error("Update profile error:", err);
        }
    });

    // Delete Account
    const deleteAccountBtn = document.getElementById('delete-account-btn');
    deleteAccountBtn.addEventListener('click', async () => {
        if (!confirm("WARNING: Are you sure you want to delete your account? This action is permanent!")) return;

        try {
            const res = await customFetch(`/users/delete/${currentUser.user_id}/`, {
                method: 'DELETE'
            });

            if (res.ok) {
                showToast("Account deleted successfully.", "success");
                localStorage.removeItem('currentUser');
                setTimeout(() => {
                    window.location.href = 'index.html';
                }, 1500);
            } else {
                const data = await res.json();
                showToast(data.error || "Account deletion failed.", "error");
            }
        } catch (err) {
            console.error("Delete account error:", err);
        }
    });

    // Logout Action
    document.getElementById('logout-btn').addEventListener('click', async () => {
        try {
            await customFetch('/users/logout/', { method: 'POST' });
        } catch(e) {}
        
        localStorage.removeItem('currentUser');
        showToast("Logged out successfully.");
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 1000);
    });

    // Initialization
    checkAuthentication();
    loadSidebarList();
    
    // Refresh lists and status badges every 4 seconds
    sidebarInterval = setInterval(loadSidebarList, 4000);
}
