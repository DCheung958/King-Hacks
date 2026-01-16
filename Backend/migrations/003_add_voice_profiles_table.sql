-- Migration: Add voice_profiles table for multiple voice profiles per user
-- This allows users to have multiple voice profiles and choose which one to use

CREATE TABLE IF NOT EXISTS voice_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    voice_id VARCHAR(255) NOT NULL,
    voice_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_voice_profiles_user_id ON voice_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_voice_profiles_user_active ON voice_profiles(user_id, is_active) WHERE is_active = TRUE;

-- Add comments for documentation
COMMENT ON TABLE voice_profiles IS 'Stores multiple voice profiles per user, allowing users to choose which voice to use';
COMMENT ON COLUMN voice_profiles.voice_id IS 'ElevenLabs voice ID for the cloned voice';
COMMENT ON COLUMN voice_profiles.voice_name IS 'Name of the voice profile';
COMMENT ON COLUMN voice_profiles.is_active IS 'Indicates which voice profile is currently active for the user (only one should be active per user)';

-- Migrate existing voice profiles from users table to voice_profiles table
-- This ensures existing users don't lose their voice profiles
INSERT INTO voice_profiles (user_id, voice_id, voice_name, is_active, created_at)
SELECT id, voice_id, voice_name, TRUE, created_at
FROM users
WHERE voice_id IS NOT NULL AND voice_name IS NOT NULL
ON CONFLICT DO NOTHING;

