# Audio File Setup

## Sample Audio File

The application expects a sample audio file at `/sample.mp3` in the public folder.

### Option 1: Add Your Own Audio File

Place a calming audio file (MP3 format) named `sample.mp3` in the `Frontend/public/` directory.

### Option 2: Use the Data URI Fallback

If you don't have an audio file yet, you can modify `src/services/ttsService.js` to use the built-in data URI fallback by uncommenting the alternative return statement.

### For Production

In the real implementation, this service will call the ElevenLabs API to synthesize speech from text, so this file is only needed for the frontend-only mock implementation.

