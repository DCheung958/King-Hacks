import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './VoiceProfileSelection.css';

const VoiceProfileSelection = ({ onClose, onNavigateToSetup }) => {
  const navigate = useNavigate();
  const [voiceProfile, setVoiceProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing voice profile
    const voiceId = localStorage.getItem('voice_id');
    const voiceName = localStorage.getItem('voice_name');
    
    if (voiceId && voiceName) {
      setVoiceProfile({
        id: voiceId,
        name: voiceName
      });
    }
    
    setLoading(false);
  }, []);

  // Refresh profile when modal opens
  useEffect(() => {
    const voiceId = localStorage.getItem('voice_id');
    const voiceName = localStorage.getItem('voice_name');
    
    if (voiceId && voiceName) {
      setVoiceProfile({
        id: voiceId,
        name: voiceName
      });
    } else {
      setVoiceProfile(null);
    }
  }, [onClose]);

  const handleCreateNew = () => {
    onClose(); // Close modal first
    if (onNavigateToSetup) {
      // Small delay to ensure modal closes before navigation
      setTimeout(() => {
        onNavigateToSetup();
      }, 100);
    } else {
      setTimeout(() => {
        navigate('/voice-profile', { state: { isNewProfile: true } });
      }, 100);
    }
  };

  const handleEdit = () => {
    onClose(); // Close modal first
    if (onNavigateToSetup) {
      // Small delay to ensure modal closes before navigation
      setTimeout(() => {
        onNavigateToSetup();
      }, 100);
    } else {
      setTimeout(() => {
        navigate('/voice-profile', { state: { isNewProfile: true, editExisting: true } });
      }, 100);
    }
  };

  return (
    <div className="voice-profile-modal-overlay" onClick={onClose}>
      <div className="voice-profile-modal" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close-button" onClick={onClose}>×</button>
        
        <div className="modal-header">
          <h2 className="modal-title">Voice Profile</h2>
        </div>

        {loading ? (
          <div className="modal-loading">Loading...</div>
        ) : voiceProfile ? (
          <div className="modal-content">
            <div className="modal-profile-info">
              <div className="modal-profile-icon">🎤</div>
              <div className="modal-profile-details">
                <h3 className="modal-profile-name">{voiceProfile.name}</h3>
                <p className="modal-profile-status">Active</p>
              </div>
            </div>
            
            <div className="modal-actions">
              <button 
                className="modal-button modal-button-primary"
                onClick={handleEdit}
              >
                Create New Profile
              </button>
            </div>
          </div>
        ) : (
          <div className="modal-content">
            <div className="modal-no-profile">
              <div className="modal-profile-icon">🎤</div>
              <p className="modal-no-profile-text">
                No voice profile yet. Create one to personalize your experience.
              </p>
            </div>
            
            <button 
              className="modal-button modal-button-primary"
              onClick={handleCreateNew}
            >
              Create Voice Profile
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default VoiceProfileSelection;

