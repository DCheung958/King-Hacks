import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './VoiceProfileSelection.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const VoiceProfileSelection = ({ onClose, onNavigateToSetup }) => {
  const navigate = useNavigate();
  const [voiceProfiles, setVoiceProfiles] = useState([]);
  const [activeProfile, setActiveProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activating, setActivating] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null); // { profileId, profileName }
  const dropdownRef = useRef(null);
  
  // Check if this is being used as a page (no onClose prop) vs dropdown component
  const isPageView = !onClose;

  // Helper function to check if a string is a valid UUID
  const isValidUUID = (str) => {
    if (!str || typeof str !== 'string') return false;
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    return uuidRegex.test(str);
  };

  const loadVoiceProfiles = async () => {
    const userId = localStorage.getItem('user_id');
    
    // First, check localStorage for voice profiles array (works even if API fails)
    try {
      const storedProfiles = localStorage.getItem('voice_profiles');
      if (storedProfiles) {
        const profiles = JSON.parse(storedProfiles);
        if (profiles && profiles.length > 0) {
          // Filter out profiles with invalid IDs (like "local" or "local-new")
          const validProfiles = profiles.filter(p => isValidUUID(p.id));
          if (validProfiles.length > 0) {
            setVoiceProfiles(validProfiles);
            // Find active profile
            const active = validProfiles.find(p => p.is_active) || validProfiles[0];
            if (active) {
              setActiveProfile(active);
              // Update voice_id and voice_name for backward compatibility
              localStorage.setItem('voice_id', active.voice_id);
              localStorage.setItem('voice_name', active.voice_name);
            }
          }
        }
      }
    } catch (e) {
      console.error('Error loading voice profiles from localStorage:', e);
    }
    
    if (!userId) {
      setLoading(false);
      return;
    }

    // Try to load from API (for multiple profiles support)
    try {
      const response = await fetch(`${API_BASE_URL}/api/users/${userId}/voice-profiles`);
      if (response.ok) {
        const profiles = await response.json();
        if (profiles && profiles.length > 0) {
          // Filter out any profiles with invalid IDs and update state
          const validProfiles = profiles.filter(p => isValidUUID(p.id));
          if (validProfiles.length > 0) {
            setVoiceProfiles(validProfiles);
            // Find active profile
            const active = validProfiles.find(p => p.is_active) || validProfiles[0];
            if (active) {
              setActiveProfile(active);
              // Update localStorage with all valid profiles and active profile
              localStorage.setItem('voice_profiles', JSON.stringify(validProfiles));
              localStorage.setItem('voice_id', active.voice_id);
              localStorage.setItem('voice_name', active.voice_name);
            }
          } else {
            // No valid profiles from API, keep what we have from localStorage
            console.warn('No valid voice profiles found in API response');
          }
        } else {
          // No profiles from API, keep what we have from localStorage
          console.warn('No voice profiles found in API response');
        }
      } else {
        // API failed (404 or other error) - we already loaded from localStorage above
        console.warn(`Failed to load voice profiles from API (${response.status}), using localStorage`);
        const errorText = await response.text().catch(() => '');
        console.warn('Error response:', errorText);
      }
    } catch (error) {
      console.error('Error loading voice profiles:', error);
      // We already loaded from localStorage above, so continue
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Load profiles immediately (checks localStorage first, then API)
    loadVoiceProfiles();
  }, []);

  // Refresh profiles when dropdown opens
  useEffect(() => {
    if (!isPageView) {
      loadVoiceProfiles();
    }
  }, [onClose, isPageView]);

  // Close dropdown when clicking outside (only if used as dropdown)
  useEffect(() => {
    if (isPageView) return;
    
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        onClose?.();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [onClose, isPageView]);

  const handleActivateProfile = async (profileId) => {
    const userId = localStorage.getItem('user_id');
    if (!userId) return;

    // Only allow activation of profiles with valid UUID IDs (not local profiles)
    if (!isValidUUID(profileId)) {
      console.warn('Cannot activate profile with invalid ID:', profileId);
      return;
    }

    setActivating(profileId);
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/users/${userId}/voice-profiles/${profileId}/activate`,
        { method: 'POST' }
      );
      
      if (response.ok) {
        const updatedProfile = await response.json();
        // Update state - mark all as inactive, then activate the selected one
        setVoiceProfiles(prev => {
          const updated = prev.map(p => ({
            ...p,
            is_active: p.id === profileId
          }));
          // Update localStorage with updated profiles
          localStorage.setItem('voice_profiles', JSON.stringify(updated));
          return updated;
        });
        setActiveProfile(updatedProfile);
        // Update localStorage with active profile info
        localStorage.setItem('voice_id', updatedProfile.voice_id);
        localStorage.setItem('voice_name', updatedProfile.voice_name);
        
        // Reload profiles to ensure sync with backend
        await loadVoiceProfiles();
      } else {
        console.error('Failed to activate voice profile');
        const errorText = await response.text();
        console.error('Error response:', errorText);
      }
    } catch (error) {
      console.error('Error activating voice profile:', error);
    } finally {
      setActivating(null);
    }
  };

  const handleDeleteProfile = async (profileId) => {
    const userId = localStorage.getItem('user_id');
    if (!userId) return;

    // Only allow deletion of profiles with valid UUID IDs
    if (!isValidUUID(profileId)) {
      console.warn('Cannot delete profile with invalid ID:', profileId);
      return;
    }

    setDeleting(profileId);
    try {
      // Check if we're deleting the active profile
      const profileToDelete = voiceProfiles.find(p => p.id === profileId);
      const wasActive = profileToDelete?.is_active;
      
      const response = await fetch(
        `${API_BASE_URL}/api/users/${userId}/voice-profiles/${profileId}`,
        { method: 'DELETE' }
      );
      
      if (response.ok) {
        // Remove from state
        setVoiceProfiles(prev => {
          const updated = prev.filter(p => p.id !== profileId);
          
          // If we deleted the active profile and there are remaining profiles, activate the first one
          if (wasActive && updated.length > 0) {
            const newActiveId = updated[0].id;
            // Activate the first remaining profile via API
            fetch(
              `${API_BASE_URL}/api/users/${userId}/voice-profiles/${newActiveId}/activate`,
              { method: 'POST' }
            ).then(async (activateResponse) => {
              if (activateResponse.ok) {
                const newActive = await activateResponse.json();
                localStorage.setItem('voice_id', newActive.voice_id);
                localStorage.setItem('voice_name', newActive.voice_name);
                setActiveProfile(newActive);
              }
            }).catch(err => {
              console.error('Error activating new profile after delete:', err);
            });
          } else if (updated.length === 0) {
            // No profiles left
            localStorage.removeItem('voice_id');
            localStorage.removeItem('voice_name');
            localStorage.removeItem('voice_profiles');
            setActiveProfile(null);
          }
          
          // Update localStorage with updated profiles
          localStorage.setItem('voice_profiles', JSON.stringify(updated));
          
          return updated;
        });
        
        // Close confirmation dialog
        setDeleteConfirm(null);
        
        // Reload profiles to ensure sync with backend
        await loadVoiceProfiles();
      } else {
        console.error('Failed to delete voice profile');
        const errorText = await response.text();
        console.error('Error response:', errorText);
      }
    } catch (error) {
      console.error('Error deleting voice profile:', error);
    } finally {
      setDeleting(null);
    }
  };

  const handleDeleteClick = (profileId, profileName, e) => {
    e.stopPropagation(); // Prevent triggering other handlers
    setDeleteConfirm({ profileId, profileName });
  };

  const handleCancelDelete = () => {
    setDeleteConfirm(null);
  };

  const handleCreateNew = () => {
    if (!isPageView) {
      onClose?.();
    }
    if (onNavigateToSetup) {
      setTimeout(() => {
        onNavigateToSetup();
      }, 100);
    } else {
      setTimeout(() => {
        navigate('/voice-profile', { state: { isNewProfile: true } });
      }, 100);
    }
  };

  // Auto-redirect to chat if voice profile exists (for page view)
  useEffect(() => {
    if (isPageView) {
      const voiceId = localStorage.getItem('voice_id');
      const voiceName = localStorage.getItem('voice_name');
      
      if (voiceId && voiceName) {
        // Show success message for 2 seconds, then redirect
        const timer = setTimeout(() => {
          navigate('/chat');
        }, 2000);
        return () => clearTimeout(timer);
      } else if (!loading) {
        // No voice profile and not loading - redirect to setup
        const timer = setTimeout(() => {
          navigate('/voice-profile');
        }, 1000);
        return () => clearTimeout(timer);
      }
    }
  }, [isPageView, loading, navigate]);

  // If used as a page, render a full page layout
  if (isPageView) {
    const voiceId = localStorage.getItem('voice_id');
    const voiceName = localStorage.getItem('voice_name');
    
    if (loading && !voiceId) {
      return (
        <div className="voice-profile-selection-page" style={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '2rem',
          backgroundColor: '#f5f5f5'
        }}>
          <div style={{ fontSize: '1.2rem', color: '#666' }}>Loading...</div>
        </div>
      );
    }
    
    if (voiceId && voiceName) {
      return (
        <div className="voice-profile-selection-page" style={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '2rem',
          backgroundColor: '#f5f5f5'
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '3rem',
            borderRadius: '12px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
            textAlign: 'center',
            maxWidth: '500px'
          }}>
            <h1 style={{ marginBottom: '1rem', color: '#20b2aa' }}>Voice Profile Created!</h1>
            <p style={{ marginBottom: '2rem', color: '#666' }}>
              Your voice profile "{voiceName}" has been successfully created.
            </p>
            <p style={{ marginBottom: '1rem', color: '#999', fontSize: '0.9rem' }}>
              Redirecting to chat...
            </p>
          </div>
        </div>
      );
    }
    
    return (
      <div className="voice-profile-selection-page" style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem',
        backgroundColor: '#f5f5f5'
      }}>
        <div style={{
          backgroundColor: 'white',
          padding: '3rem',
          borderRadius: '12px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
          textAlign: 'center',
          maxWidth: '500px'
        }}>
          <h1 style={{ marginBottom: '1rem' }}>No Voice Profile</h1>
          <p style={{ marginBottom: '2rem', color: '#666' }}>
            No voice profile found. Redirecting to setup...
          </p>
        </div>
      </div>
    );
  }

  // Otherwise render as dropdown component
  return (
    <div className="voice-profile-dropdown" ref={dropdownRef} onClick={(e) => e.stopPropagation()}>
      {loading ? (
        <div className="dropdown-loading">Loading...</div>
      ) : (
        <div className="dropdown-content">
          {voiceProfiles.length > 0 && (
            <>
              <div className="dropdown-header">
                <h3 className="dropdown-title">Voice Profiles</h3>
              </div>
              
              <div className="dropdown-profiles-list">
                {voiceProfiles
                  .filter(profile => isValidUUID(profile.id)) // Only show profiles with valid UUIDs
                  .map((profile) => (
                    <div
                      key={profile.id}
                      className={`dropdown-profile-item ${profile.is_active ? 'active' : ''}`}
                    >
                      <div className="dropdown-profile-info">
                        <div className="dropdown-profile-details">
                          <h4 className="dropdown-profile-name">{profile.voice_name}</h4>
                          {profile.is_active && (
                            <span className="dropdown-profile-badge">Active</span>
                          )}
                        </div>
                      </div>
                      <div className="dropdown-profile-actions">
                        {!profile.is_active && (
                          <button
                            className="dropdown-activate-button"
                            onClick={() => handleActivateProfile(profile.id)}
                            disabled={activating === profile.id || deleting === profile.id}
                          >
                            {activating === profile.id ? 'Activating...' : 'Use This Voice'}
                          </button>
                        )}
                        <button
                          className="dropdown-delete-button"
                          onClick={(e) => handleDeleteClick(profile.id, profile.voice_name, e)}
                          disabled={activating === profile.id || deleting === profile.id}
                          title="Delete voice profile"
                        >
                          ×
                        </button>
                      </div>
                    </div>
                  ))}
              </div>
              
              {/* Delete Confirmation Modal */}
              {deleteConfirm && (
                <div className="delete-confirm-overlay" onClick={handleCancelDelete}>
                  <div className="delete-confirm-modal" onClick={(e) => e.stopPropagation()}>
                    <h3 className="delete-confirm-title">Delete Voice Profile?</h3>
                    <p className="delete-confirm-message">
                      Are you sure you want to delete "{deleteConfirm.profileName}"? This action cannot be undone.
                    </p>
                    <div className="delete-confirm-actions">
                      <button
                        className="delete-confirm-cancel"
                        onClick={handleCancelDelete}
                        disabled={deleting === deleteConfirm.profileId}
                      >
                        Cancel
                      </button>
                      <button
                        className="delete-confirm-delete"
                        onClick={() => handleDeleteProfile(deleteConfirm.profileId)}
                        disabled={deleting === deleteConfirm.profileId}
                      >
                        {deleting === deleteConfirm.profileId ? 'Deleting...' : 'Delete'}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
          
          <div className="dropdown-actions">
            <button 
              className="dropdown-button dropdown-button-primary"
              onClick={handleCreateNew}
            >
              {voiceProfiles.length > 0 ? 'Create New Profile' : 'Create Voice Profile'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default VoiceProfileSelection;
