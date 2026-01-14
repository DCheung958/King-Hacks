# AI Response Generation - Implementation Guide

## Overview

The therapeutic response generation now uses **DialoGPT-medium** (a free, open-source conversational model from Microsoft) to generate empathetic, context-aware responses.

## Model Details

- **Model**: `microsoft/DialoGPT-medium` (DialoGPT-medium conversational model)
- **Size**: ~350MB
- **Cost**: Completely FREE (runs locally)
- **Requirements**: transformers, torch (already installed)
- **Speed**: Runs on CPU (first response may take 5-10 seconds, subsequent responses faster)
- **Training**: Trained on 147M multi-turn Reddit dialogues - optimized for conversation

## How It Works

1. **Prompt Engineering**: The model receives a carefully crafted prompt that includes:
   - Instructions to act as a compassionate therapist
   - The user's input text
   - Detected emotion (if available)
   - Response format instructions

2. **Generation**: DialoGPT-medium generates a response using:
   - Temperature: 0.7 (balanced creativity)
   - Top-p sampling: 0.9 (nucleus sampling)
   - Max length: 100 tokens
   - Repetition penalty: Avoids repeating 2-grams

3. **Post-processing**: 
   - Extracts only the therapist's response
   - Cleans and formats the output
   - Limits length to ~200 characters
   - Falls back to mock if generation fails

## Fallback Behavior

- If the model fails to load → Uses mock responses (predefined list)
- If generation fails at runtime → Falls back to mock responses
- Graceful degradation ensures the API always responds

## Alternative Models (Optional)

You can change the model in `response_model.py`:

```python
# Current (conversational, 350MB) - Recommended
MODEL_NAME = "microsoft/DialoGPT-medium"

# General purpose (fast, 500MB)
MODEL_NAME = "gpt2"

# Better quality (slower, 1.4GB)
MODEL_NAME = "gpt2-medium"
```

## First Run

On first run, the model will be downloaded from Hugging Face (~350MB). This happens automatically and only needs to happen once.

## Testing

The model integrates seamlessly with the existing `/api/respond` endpoint. No API changes needed!
