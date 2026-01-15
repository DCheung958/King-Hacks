# Google OAuth Setup Guide

This guide will walk you through setting up Google OAuth authentication for Echocare.

## Prerequisites

- A Google account
- Access to Google Cloud Console
- Your backend and frontend URLs

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click "New Project"
4. Enter a project name (e.g., "Echocare")
5. Click "Create"

## Step 2: Enable Google+ API

1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "Google+ API" or "Google Identity Services"
3. Click on it and click "Enable"

## Step 3: Configure OAuth Consent Screen

1. Go to "APIs & Services" > "OAuth consent screen"
2. Choose "External" (unless you have a Google Workspace account)
3. Click "Create"
4. Fill in the required information:
   - **App name**: Echocare
   - **User support email**: Your email
   - **Developer contact information**: Your email
5. Click "Save and Continue"
6. On the "Scopes" page, click "Add or Remove Scopes"
   - Add: `email`, `profile`, `openid`
7. Click "Save and Continue"
8. On the "Test users" page (for testing), add your email address
9. Click "Save and Continue"
10. Review and click "Back to Dashboard"

## Step 4: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Choose "Web application" as the application type
4. Give it a name (e.g., "Echocare Web Client")
5. Add **Authorized JavaScript origins**:
   - `http://localhost:5173` (for local development)
   - `http://localhost:8000` (for backend)
   - Your production frontend URL (when deployed)
   - Your production backend URL (when deployed)
6. Add **Authorized redirect URIs**:
   - `http://localhost:8000/api/auth/google/callback` (for local development)
   - Your production backend URL + `/api/auth/google/callback` (when deployed)
   - Example: `https://your-backend.com/api/auth/google/callback`
7. Click "Create"
8. **IMPORTANT**: Copy the **Client ID** and **Client Secret** - you'll need these!

## Step 5: Configure Environment Variables

### Backend (.env file)

Add these variables to your `Backend/.env` file:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here

# Backend URL (for OAuth redirect)
BACKEND_URL=http://localhost:8000

# Frontend URL (for OAuth callback redirect)
FRONTEND_URL=http://localhost:5173
```

**For production**, update these URLs to your actual domain:
```env
BACKEND_URL=https://api.yourapp.com
FRONTEND_URL=https://yourapp.com
```

### Frontend (.env file)

Add this to your `Frontend/.env` file (if not already present):

```env
VITE_API_URL=http://localhost:8000
```

**For production**:
```env
VITE_API_URL=https://api.yourapp.com
```

## Step 6: Install Dependencies

### Backend

```bash
cd Backend
pip install -r requirements.txt
```

This will install:
- `google-auth`
- `google-auth-oauthlib`
- `google-auth-httplib2`
- `httpx`

### Frontend

No additional dependencies needed - the implementation uses native fetch API.

## Step 7: Test the Integration

1. Start your backend:
   ```bash
   cd Backend
   uvicorn main:app --reload
   ```

2. Start your frontend:
   ```bash
   cd Frontend
   npm run dev
   ```

3. Navigate to the sign-in or sign-up page
4. Click "Continue with Google"
5. You should be redirected to Google's sign-in page
6. After signing in, you'll be redirected back to the app

## Troubleshooting

### "redirect_uri_mismatch" Error

- Make sure the redirect URI in Google Cloud Console exactly matches: `http://localhost:8000/api/auth/google/callback`
- Check that there are no trailing slashes
- Ensure the protocol (http/https) matches

### "invalid_client" Error

- Verify your `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correct
- Make sure there are no extra spaces in your `.env` file
- Restart your backend server after updating `.env`

### OAuth Consent Screen Issues

- If you see "This app isn't verified", you can click "Advanced" > "Go to [App Name] (unsafe)" to continue testing
- For production, you'll need to submit your app for verification

### CORS Issues

- Make sure your backend CORS settings allow your frontend origin
- Check `main.py` for CORS middleware configuration

## Production Deployment

1. **Update OAuth Consent Screen**:
   - Complete all required fields
   - Submit for verification (if required)
   - Add your production domain

2. **Update Credentials**:
   - Add production URLs to Authorized JavaScript origins
   - Add production callback URL to Authorized redirect URIs

3. **Update Environment Variables**:
   - Set `BACKEND_URL` to your production backend URL
   - Set `FRONTEND_URL` to your production frontend URL
   - Keep credentials secure (use environment variables, not hardcoded)

4. **Security**:
   - Never commit `.env` files to version control
   - Use secure environment variable management (e.g., AWS Secrets Manager, Azure Key Vault)
   - Enable HTTPS for production

## How It Works

1. User clicks "Continue with Google" button
2. Frontend calls `/api/auth/google` endpoint
3. Backend returns Google OAuth authorization URL
4. User is redirected to Google's sign-in page
5. User authorizes the app
6. Google redirects to `/api/auth/google/callback` with an authorization code
7. Backend exchanges code for access token
8. Backend fetches user info from Google
9. Backend creates or finds user in database
10. Backend creates JWT token
11. Backend redirects to frontend with token in URL
12. Frontend extracts token and stores it
13. User is logged in!

## Support

If you encounter issues:
1. Check the browser console for errors
2. Check backend logs for detailed error messages
3. Verify all environment variables are set correctly
4. Ensure Google Cloud Console settings match your URLs exactly
