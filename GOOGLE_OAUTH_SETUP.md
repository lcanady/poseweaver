# Google OAuth Setup for PoseWeaver

This guide explains how to set up Google OAuth authentication for PoseWeaver.

## Prerequisites

- Google Cloud Console account
- PoseWeaver frontend and backend running locally

## Step 1: Create Google OAuth Credentials

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google+ API" and enable it
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Web application"
   - Add authorized JavaScript origins:
     - `http://localhost:3000` (for development)
     - Your production domain (for production)
   - Add authorized redirect URIs:
     - `http://localhost:3000` (for development)
     - Your production domain (for production)
   - Save and copy the Client ID

## Step 2: Configure Frontend Environment

Create a `.env.local` file in the frontend directory with:

```env
# Google OAuth Configuration
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id_here

# API Configuration (if different from default)
NEXT_PUBLIC_API_URL=http://localhost:5001
```

Replace `your_google_client_id_here` with the Client ID from Step 1.

## Step 3: Test the Implementation

1. Start the backend server:
   ```bash
   cd backend
   python app.py
   ```

2. Start the frontend server:
   ```bash
   cd frontend
   npm run dev
   ```

3. Navigate to `http://localhost:3000/login`
4. Click the "Sign in with Google" button
5. Complete the Google OAuth flow
6. You should be redirected to the dashboard upon successful authentication

## How It Works

### Frontend Flow
1. User clicks "Sign in with Google" button
2. `GoogleAuthService.signInWithPopup()` opens Google OAuth popup
3. User completes Google authentication
4. Google returns user information (email, name, picture, Google ID)
5. Frontend sends this data to backend `/api/auth/google` endpoint
6. Backend creates/updates user and returns JWT tokens
7. Frontend stores tokens and redirects to dashboard

### Backend Flow
1. `/api/auth/google` endpoint receives Google user data
2. `AuthService.authenticate_or_create_google_user()` method:
   - Finds existing user by email OR creates new user
   - Updates user profile with Google information if needed
   - Generates JWT access and refresh tokens
3. Returns user data and tokens to frontend

## Security Features

- JWT tokens for secure API authentication
- Google OAuth for trusted identity verification
- Automatic user creation/update with Google profile data
- Session management with token refresh capability

## Troubleshooting

### "Google Client ID not configured" Error
- Ensure `NEXT_PUBLIC_GOOGLE_CLIENT_ID` is set in `.env.local`
- Restart the frontend development server after adding environment variables

### "Failed to load Google Identity Services" Error
- Check internet connection
- Ensure Google APIs are accessible
- Verify the Google Client ID is valid

### Backend Authentication Errors
- Check backend logs for detailed error messages
- Ensure MongoDB is running and accessible
- Verify backend API endpoints are responding

### CORS Issues
- Ensure frontend URL is added to Google OAuth authorized origins
- Check backend CORS configuration

## Production Deployment

For production deployment:

1. Update Google OAuth credentials with production domain
2. Set production environment variables
3. Ensure HTTPS is enabled for OAuth security
4. Update CORS settings for production domain

## API Endpoints

### POST /api/auth/google
Authenticates or creates user with Google OAuth data.

**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "User Name",
  "picture": "https://example.com/avatar.jpg",
  "google_id": "google_user_id"
}
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "display_name": "User Name",
    "avatar_url": "https://example.com/avatar.jpg",
    "is_active": true
  },
  "access_token": "jwt_access_token",
  "refresh_token": "jwt_refresh_token"
}
```
