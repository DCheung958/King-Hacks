# LLaMA 3.1 8B Instruct Setup Guide

## Overview

Echocare now uses **meta-llama/Llama-3.1-8b-Instruct** for generating therapeutic responses. This is a powerful instruction-tuned language model that provides high-quality, empathetic responses.

## Prerequisites

1. **Hugging Face Account**: You need a Hugging Face account with access to LLaMA 3.1 models
2. **Hugging Face CLI**: Install and log in to Hugging Face

## Setup Steps

### 1. Install/Update Dependencies

Make sure you have the latest versions of transformers and huggingface_hub:

```bash
pip install -U transformers huggingface_hub torch
```

### 2. Log in to Hugging Face

You must be logged in to Hugging Face to access LLaMA 3.1 models:

```bash
huggingface-cli login
```

Enter your Hugging Face access token when prompted. You can get your token from: https://huggingface.co/settings/tokens

**Note**: You need to request access to LLaMA 3.1 models on the Hugging Face model page: https://huggingface.co/meta-llama/Llama-3.1-8b-Instruct

### 3. Model Loading

The model will be automatically downloaded and loaded when you start the backend. The first time you run it, the model files (~16GB) will be downloaded from Hugging Face.

**Important**: Make sure you have enough disk space and RAM:
- **Disk Space**: ~16GB for the model files
- **RAM**: At least 16GB recommended (8GB minimum)
- **VRAM** (if using GPU): At least 8GB for GPU acceleration

### 4. Running the Backend

Start the backend as usual:

```bash
cd Backend
python main.py
```

The model will load automatically. You'll see a message like:
```
Loading response generation model (meta-llama/Llama-3.1-8b-Instruct)...
Response generation model loaded successfully!
```

## Model Configuration

The model is configured with:
- **Device**: Auto (uses GPU if available, otherwise CPU)
- **Precision**: float16 (for memory efficiency)
- **Temperature**: 0.7 (balanced for empathy and naturalness)
- **Top-p**: 0.9 (nucleus sampling)
- **Max Tokens**: Adaptive based on emotional intensity (20-200 tokens)

## Troubleshooting

### "Model not found" or Authentication Error

- Make sure you're logged in: `huggingface-cli login`
- Request access to the model: https://huggingface.co/meta-llama/Llama-3.1-8b-Instruct
- Check your Hugging Face token has the correct permissions

### Out of Memory Errors

- The model requires significant memory. Try:
  - Using a GPU if available (automatically used if detected)
  - Reducing batch size or max tokens in the code
  - Using CPU with lower precision (requires code changes)

### Slow Generation

- First generation is slower due to model loading
- GPU acceleration significantly speeds up generation
- Subsequent generations are faster as the model is cached in memory

## Fallback Behavior

If the model fails to load, the system will:
1. Print a warning message
2. Fall back to mock responses
3. Continue running (allows you to fix the issue without restarting)

## Performance Notes

- **First Response**: 5-15 seconds (model loading + generation)
- **Subsequent Responses**: 1-5 seconds (generation only)
- **GPU Acceleration**: Can reduce generation time by 3-5x

## Alternative Models

If LLaMA 3.1 8B is too resource-intensive, you can modify `response_model.py` to use:
- Smaller models (e.g., LLaMA 3.1 70B would be even larger)
- Quantized versions (4-bit/8-bit quantization)
- Other instruction-tuned models compatible with the chat format

