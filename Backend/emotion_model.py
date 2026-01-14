"""
Emotion Detection using Hugging Face Transformers
Uses bhadresh-savani/distilbert-base-uncased-emotion model for emotion classification
"""

# Try to load the model, but gracefully handle if transformers/torch not installed
EMOTION_MODEL_AVAILABLE = False
tokenizer = None
model = None

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    import torch.nn.functional as F
    
    # Load model and tokenizer once (expensive, do it at startup)
    print("Loading emotion detection model...")
    tokenizer = AutoTokenizer.from_pretrained("bhadresh-savani/distilbert-base-uncased-emotion")
    model = AutoModelForSequenceClassification.from_pretrained("bhadresh-savani/distilbert-base-uncased-emotion")
    model.eval()  # Set to evaluation mode
    EMOTION_MODEL_AVAILABLE = True
    print("Emotion detection model loaded successfully!")
except ImportError:
    print("Warning: transformers or torch not installed. Emotion detection will use mock implementation.")
    print("Install with: pip install transformers torch")
except Exception as e:
    print(f"Warning: Failed to load emotion detection model: {e}")
    print("Falling back to mock emotion detection.")


def detect_emotion(text: str):
    """
    Detect emotion from text using Hugging Face model
    
    Args:
        text: Input text to analyze
        
    Returns:
        tuple: (emotion_label, confidence) where emotion_label is lowercase emotion name
    """
    if not EMOTION_MODEL_AVAILABLE or tokenizer is None or model is None:
        raise RuntimeError("Emotion model not available. Use mock_detect_emotion instead.")
    
    # Tokenize input
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128, padding=True)
    
    # Get predictions
    with torch.no_grad():  # Disable gradient computation for inference
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=1)
        confidence, predicted_class = torch.max(probs, dim=1)
        
    # Get emotion label from model config
    emotion_label = model.config.id2label[predicted_class.item()]
    confidence_value = confidence.item()
    
    # Return lowercase emotion label and confidence
    return emotion_label.lower(), confidence_value

