"""
Quick script to check if GPU is available and being used
Run this to verify your GPU setup
"""

import sys

try:
    import torch
    print("=" * 60)
    print("GPU/CPU CHECK")
    print("=" * 60)
    
    # Check if CUDA is available
    cuda_available = torch.cuda.is_available()
    print(f"CUDA Available: {cuda_available}")
    
    if cuda_available:
        print(f"CUDA Version: {torch.version.cuda}")
        print(f"Number of GPUs: {torch.cuda.device_count()}")
        
        for i in range(torch.cuda.device_count()):
            print(f"\nGPU {i}:")
            print(f"  Name: {torch.cuda.get_device_name(i)}")
            print(f"  Memory Total: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.2f} GB")
            print(f"  Memory Allocated: {torch.cuda.memory_allocated(i) / 1024**3:.2f} GB")
            print(f"  Memory Cached: {torch.cuda.memory_reserved(i) / 1024**3:.2f} GB")
    else:
        print("\n⚠️  CUDA is NOT available!")
        print("Your PyTorch installation is CPU-only.")
        print("\nTo fix this:")
        print("1. Check if you have an NVIDIA GPU: nvidia-smi")
        print("2. Install PyTorch with CUDA support")
        print("3. See Backend/INSTALL_PYTORCH_CUDA.md for instructions")
    
    # Check for accelerate
    try:
        import accelerate
        print(f"\nAccelerate: Available (version {accelerate.__version__})")
    except ImportError:
        print("\nAccelerate: NOT installed")
        print("  Install with: pip install accelerate")
    
    # Check for bitsandbytes
    try:
        import bitsandbytes
        print(f"BitsAndBytes: Available")
    except ImportError:
        print("BitsAndBytes: NOT installed")
        print("  Install with: pip install bitsandbytes")
        print("  (Required for 8-bit quantization on GPU)")
    
    print("\n" + "=" * 60)
    print("To verify GPU usage during inference:")
    print("1. Run your backend and check startup messages")
    print("2. Look for 'Using GPU with...' or 'Using CPU mode...'")
    print("3. In another terminal, run: nvidia-smi -l 1")
    print("   (This shows GPU usage in real-time)")
    print("=" * 60)
    
except ImportError:
    print("ERROR: PyTorch is not installed!")
    print("Install with: pip install torch")
    sys.exit(1)

