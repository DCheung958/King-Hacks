-- Migration: Add voice profile columns to users table
-- Adds voice_id and voice_name to store user's cloned voice information

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS voice_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS voice_name VARCHAR(255);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_voice_id ON users(voice_id) WHERE voice_id IS NOT NULL;

-- Add comment for documentation
COMMENT ON COLUMN users.voice_id IS 'ElevenLabs voice ID for the user''s cloned voice';
COMMENT ON COLUMN users.voice_name IS 'Name of the user''s cloned voice profile';

