"""
AI-Based Therapeutic Response Generation using Hugging Face Transformers
Uses GPT-2 for generating empathetic therapeutic responses
"""

# Try to load the model, but gracefully handle if transformers/torch not installed
RESPONSE_MODEL_AVAILABLE = False
tokenizer = None
model = None

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    
    # Load model and tokenizer once (expensive, do it at startup)
    print("Loading response generation model (DialoGPT-medium)...")
    MODEL_NAME = "microsoft/DialoGPT-medium"  # Conversational model for dialogue
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    model.eval()  # Set to evaluation mode
    
    # Add padding token if it doesn't exist
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    RESPONSE_MODEL_AVAILABLE = True
    print("Response generation model loaded successfully!")
except ImportError:
    print("Warning: transformers or torch not installed. Response generation will use mock implementation.")
    print("Install with: pip install transformers torch")
except Exception as e:
    print(f"Warning: Failed to load response generation model: {e}")
    print("Falling back to mock response generation.")


def generate_therapeutic_response(user_text: str, emotion: str = None) -> str:
    """
    Generate an empathetic therapeutic response using DialoGPT-medium
    
    Args:
        user_text: The user's input text
        emotion: Detected emotion (optional, used for context)
        
    Returns:
        Generated therapeutic response text
    """
    if not RESPONSE_MODEL_AVAILABLE or tokenizer is None or model is None:
        raise RuntimeError("Response model not available. Use mock responses instead.")
    
    # Create a therapeutic prompt (DialoGPT works well with conversational format)
    if emotion:
        prompt = f"I'm feeling {emotion}. {user_text}"
    else:
        prompt = user_text
    
    # Tokenize the prompt (DialoGPT expects EOS token for context)
    inputs = tokenizer.encode(prompt + tokenizer.eos_token, return_tensors="pt", max_length=512, truncation=True)
    
    # Generate response
    with torch.no_grad():  # Disable gradient computation for inference
        outputs = model.generate(
            inputs,
            max_length=inputs.shape[1] + 100,  # Generate up to 100 more tokens
            min_length=inputs.shape[1] + 10,   # Generate at least 10 tokens
            temperature=0.7,  # Controls randomness (0.7 is good balance)
            top_p=0.9,        # Nucleus sampling
            do_sample=True,   # Enable sampling
            pad_token_id=tokenizer.eos_token_id,
            no_repeat_ngram_size=2,  # Avoid repeating 2-grams
        )
    
    # Decode only the generated response (everything after the input)
    response = tokenizer.decode(outputs[0][:, inputs.shape[-1]:][0], skip_special_tokens=True)
    
    # Clean up the response
    response = response.strip()
    
    # Remove anything after newline or EOS
    response = response.split("\n")[0].strip()
    response = response.split(tokenizer.eos_token)[0].strip()
    
    # Ensure response is not empty
    if not response or len(response) < 10:
        response = "I understand this is difficult for you. Would you like to tell me more about what's on your mind?"
    
    # Limit response length
    if len(response) > 200:
        # Truncate at sentence boundary if possible
        sentences = response.split('. ')
        response = '. '.join(sentences[:2]) + '.'
    
    return response
