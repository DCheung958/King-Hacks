# AI Response Generation - Implementation Guide

## Overview

The therapeutic response generation uses **Llama 3.1 8B Instruct** (Meta's instruction-tuned large language model) to generate empathetic, context-aware responses.

## Model Details

- **Model**: `meta-llama/Llama-3.1-8b-Instruct` (Llama 3.1 instruction-tuned model)
- **Size**: ~16GB
- **Cost**: Completely FREE (runs locally, requires Hugging Face access)
- **Requirements**: transformers, torch, huggingface_hub (already installed)
- **Speed**: Varies based on hardware - faster with GPU acceleration
- **Context Window**: 8K tokens
- **Type**: Instruction-tuned LLM optimized for following instructions and dialogue

## Prerequisites

1. **Hugging Face Account**: You need a Hugging Face account with access to Llama 3.1 models
2. **Hugging Face Login**: Log in via `huggingface-cli login` with your access token
3. **Model Access**: Request access to Llama 3.1 models on the Hugging Face model page: https://huggingface.co/meta-llama/Llama-3.1-8b-Instruct

## How It Works

1. **Prompt Engineering**: The model receives a carefully crafted prompt in Llama chat format that includes:
   - System instruction with therapeutic guidelines
   - Persona configuration (Friend/Therapist/Family)
   - Warmth level adjustment
   - Conversation history (up to 8 previous messages)
   - Emotional trajectory and user context
   - The user's current input text

2. **Generation**: Llama 3.1 generates a response using:
   - Temperature: 0.7 (balanced creativity)
   - Top-p sampling: 0.9 (nucleus sampling)
   - Max tokens: Adaptive based on emotional intensity (20-200 tokens)
   - Repetition penalty: Avoids repetitive responses
   - Chat format: Uses Llama's chat template with system/user/assistant roles

3. **Post-processing**: 
   - Extracts and cleans the response
   - Applies therapeutic wrapper (empathy validation, directive softening)
   - Applies speech-style mirroring (subtle user style matching)
   - Falls back to mock if generation fails

## Llama Chat Format

The model uses Llama's chat format with special tokens:
- System message: Contains instructions and context
- User messages: Previous conversation turns
- Assistant messages: Previous AI responses
- Current user message: The latest input

## Fallback Behavior

- If the model fails to load → Uses mock responses (predefined list)
- If generation fails at runtime → Falls back to mock responses
- If Hugging Face authentication fails → Uses mock responses
- Graceful degradation ensures the API always responds

## Hardware Requirements

### Minimum (CPU)
- **RAM**: 16GB recommended (8GB minimum)
- **Disk Space**: ~20GB for model files
- **Speed**: Slower response times (can take 30+ seconds per response)

### Recommended (GPU)
- **VRAM**: 8GB+ (for 8-bit quantization)
- **RAM**: 16GB+
- **Disk Space**: ~20GB for model files
- **Speed**: Much faster response times (5-10 seconds per response)

## Model Loading Optimizations

The model automatically optimizes based on available resources:
- **GPU with 8-bit quantization**: Best performance (RTX 4060 8GB VRAM)
- **GPU with float16**: Good performance (if quantization not available)
- **CPU**: Works but slower

## Setup

See `Backend/LLAMA_SETUP.md` for complete setup instructions.

## Testing

The model integrates seamlessly with the existing `/api/respond` endpoint. No API changes needed!

## First Run

On first run, the model will be downloaded from Hugging Face (~16GB). This happens automatically and only needs to happen once. Make sure you:
1. Have a Hugging Face account
2. Are logged in via `huggingface-cli login`
3. Have requested access to Llama 3.1 models
4. Have enough disk space (~20GB)
