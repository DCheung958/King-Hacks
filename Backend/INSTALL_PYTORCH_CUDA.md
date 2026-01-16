# Installing PyTorch with CUDA Support

## Current Issue
Your PyTorch installation is CPU-only (`2.9.1+cpu`), which means it cannot use your RTX 4060 GPU.

## Solution: Install PyTorch with CUDA

### Step 1: Uninstall Current PyTorch
```powershell
pip uninstall torch torchvision torchaudio
```

### Step 2: Install PyTorch with CUDA

Visit https://pytorch.org/get-started/locally/ and select:
- **OS**: Windows
- **Package**: Pip
- **Language**: Python
- **Compute Platform**: CUDA 11.8 or CUDA 12.1 (check your NVIDIA driver version)

Or use one of these commands:

**For CUDA 11.8:**
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**For CUDA 12.1:**
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Step 3: Verify Installation
```powershell
$env:KMP_DUPLICATE_LIB_OK="TRUE"
python -c "import torch; print('CUDA Available:', torch.cuda.is_available()); print('CUDA Version:', torch.version.cuda if torch.cuda.is_available() else 'N/A')"
```

You should see:
- `CUDA Available: True`
- A CUDA version number (not "N/A")

### Step 4: Check Your NVIDIA Driver
Make sure you have NVIDIA drivers installed. Check with:
```powershell
nvidia-smi
```

If `nvidia-smi` works, you're good. If not, install NVIDIA drivers from: https://www.nvidia.com/Download/index.aspx

## After Installation

Once PyTorch with CUDA is installed, restart your backend and you should see:
- "Using 8-bit quantization with GPU offloading for optimal performance..." (if bitsandbytes is installed)
- Or "Using GPU with float16 precision..." (if bitsandbytes is not installed)

The model will then run on your RTX 4060 GPU, which will be much faster than CPU!

