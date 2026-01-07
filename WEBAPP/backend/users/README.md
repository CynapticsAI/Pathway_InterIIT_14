# Users App - Django Authentication & Chat System

## 📋 Overview

This Django app provides complete user authentication, profile management, and chat conversation features for the Pway Stock chatbot application.

## 🗄️ Database Schema

### Core Models

1. **CustomUser** - Extended Django user with email verification
2. **UserProfile** - User preferences and subscription management
3. **ChatConversation** - Organize chat messages
4. **ChatMessage** - Individual chat messages
5. **UserSession** - Active session tracking
6. **EmailVerificationToken** - Email verification tokens
7. **PasswordResetToken** - Password reset tokens
8. **UserActivity** - Activity logging

## 🚀 Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

Required packages:
- Django >= 5.2.8
- djangorestframework >= 3.14.0
- djangorestframework-simplejwt >= 5.3.0
- django-cors-headers >= 4.3.0
- Pillow >= 10.1.0
- requests >= 2.31.0

### 2. Run Migrations

```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

### 3. Create Superuser

```bash
python3 manage.py createsuperuser
```

### 4. Run Development Server

```bash
python3 manage.py runserver
```

## 📡 API Endpoints

### Authentication

```
POST   /api/auth/register/          - Register new user
POST   /api/auth/login/             - Login and get JWT tokens
POST   /api/auth/logout/            - Logout user
POST   /api/auth/refresh/           - Refresh JWT token
POST   /api/auth/verify-email/      - Verify email with token
POST   /api/auth/forgot-password/   - Request password reset
POST   /api/auth/reset-password/    - Reset password with token
POST   /api/auth/change-password/   - Change password (authenticated)
```

### User Profile

```
GET    /api/users/me/               - Get current user
PUT    /api/users/me/               - Update user info
GET    /api/users/me/profile/       - Get user profile
PUT    /api/users/me/profile/       - Update user profile
```

### Sessions

```
GET    /api/users/sessions/         - List active sessions
DELETE /api/users/sessions/{id}/    - Revoke specific session
```

### Chat

```
GET    /api/chat/conversations/              - List conversations
POST   /api/chat/conversations/              - Create conversation
GET    /api/chat/conversations/{id}/         - Get conversation details
PUT    /api/chat/conversations/{id}/         - Update conversation
DELETE /api/chat/conversations/{id}/         - Delete conversation
GET    /api/chat/conversations/{id}/messages/ - Get messages
POST   /api/chat/conversations/{id}/messages/create/ - Send message
```

## 🔧 Usage Examples

### Register a New User

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "password2": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "SecurePass123!"
  }'
```

Response:
```json
{
  "message": "Login successful",
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  },
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    ...
  }
}
```

### Get Current User (Authenticated)

```bash
curl -X GET http://localhost:8000/api/users/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Create a Chat Conversation

```bash
curl -X POST http://localhost:8000/api/chat/conversations/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Stock Analysis for AAPL"
  }'
```

### Send a Message

```bash
curl -X POST http://localhost:8000/api/chat/conversations/1/messages/create/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "What is the current price of AAPL?"
  }'
```

## 🔐 Authentication Flow

1. **Register**: User creates account → Email verification sent
2. **Login**: User logs in → Receives JWT access + refresh tokens
3. **Request**: Include `Authorization: Bearer <access_token>` in headers
4. **Refresh**: When access token expires, use refresh token to get new one
5. **Logout**: Invalidates all active sessions

## 🎯 Next Steps

### Step 2: Install Required Packages (You need to do this!)

```bash
cd ./pway-stock/backend
pip install djangorestframework-simplejwt django-cors-headers Pillow
```

### Step 3: Run Migrations

```bash
python3 manage.py makemigrations users
python3 manage.py migrate
```

### Step 4: Create Superuser

```bash
python3 manage.py createsuperuser
```

### Step 5: Test the API

Start the server:
```bash
python3 manage.py runserver
```

Access:
- Admin panel: http://localhost:8000/admin/
- API: http://localhost:8000/api/

## 📝 Features Included

✅ User registration with email verification
✅ JWT token authentication
✅ Password reset flow
✅ User profile management
✅ Subscription tier management
✅ Chat conversations
✅ Chat messages
✅ Session management
✅ Activity logging
✅ Admin panel with rich UI

## 🔜 To Be Implemented

- [ ] Integrate chatbot API in ChatMessageCreateView
- [ ] Add rate limiting per subscription tier
- [ ] Email notifications
- [ ] WebSocket support for real-time chat
- [ ] File attachments in chat
- [ ] Social authentication (Google, GitHub)

## 🛡️ Security Features

- Password hashing with PBKDF2
- JWT token authentication
- CORS protection
- CSRF protection
- Session management
- Activity logging
- Email verification

## 📚 Additional Notes

- All passwords are hashed before storage
- Email verification is optional (can be enforced in settings)
- Tokens expire (access: 1 hour, refresh: 7 days)
- User sessions are tracked for security
- All API endpoints support JSON

## 🐛 Troubleshooting

### Import errors for simplejwt
```bash
pip install djangorestframework-simplejwt
```

### CORS errors from frontend
Check `CORS_ALLOWED_ORIGINS` in settings.py

### Email not sending
In development, emails print to console. For production, configure SMTP in settings.py

## 📞 Support

For issues or questions, check the code comments or Django documentation.
