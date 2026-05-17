#!/usr/bin/env python3
"""
ACE-Step 1.5 Test Script
Tests basic music generation functionality.

Prerequisites:
  - ACE-Step installed in conda env 'acestep' or via uv
  - Models downloaded to /home/xsl/tools/ACE-Step-1.5/checkpoints/

Usage:
  conda activate acestep
  python test_acestep.py
"""

import os
import sys
import time

# Configuration
REPO_DIR = "/home/xsl/tools/ACE-Step-1.5"
CHECKPOINTS_DIR = os.path.join(REPO_DIR, "checkpoints")
OUTPUT_DIR = "/home/xsl/blind/audio/test_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def test_imports():
    """Test that all required packages are importable."""
    print("=" * 60)
    print("Step 1: Testing imports...")
    print("=" * 60)

    # Add repo to path
    if REPO_DIR not in sys.path:
        sys.path.insert(0, REPO_DIR)

    results = {}

    # Test torch
    try:
        import torch
        results["torch"] = f"OK (v{torch.__version__}, CUDA={torch.cuda.is_available()})"
        if torch.cuda.is_available():
            results["torch"] += f" ({torch.cuda.get_device_name(0)})"
    except ImportError as e:
        results["torch"] = f"FAIL: {e}"

    # Test transformers
    try:
        import transformers
        results["transformers"] = f"OK (v{transformers.__version__})"
    except ImportError as e:
        results["transformers"] = f"FAIL: {e}"

    # Test diffusers
    try:
        import diffusers
        results["diffusers"] = f"OK (v{diffusers.__version__})"
    except ImportError as e:
        results["diffusers"] = f"FAIL: {e}"

    # Test soundfile
    try:
        import soundfile
        results["soundfile"] = f"OK (v{soundfile.__version__})"
    except ImportError as e:
        results["soundfile"] = f"FAIL: {e}"

    # Test acestep
    try:
        import acestep
        results["acestep"] = f"OK (from {acestep.__file__})"
    except ImportError as e:
        results["acestep"] = f"FAIL: {e}"

    for k, v in results.items():
        print(f"  {k}: {v}")

    all_ok = all("OK" in v for v in results.values())
    print(f"\nImports: {'PASS' if all_ok else 'FAIL'}")
    return all_ok


def test_models_exist():
    """Test that model checkpoints are downloaded."""
    print("\n" + "=" * 60)
    print("Step 2: Checking model checkpoints...")
    print("=" * 60)

    required_components = {
        "acestep-v15-turbo": "DiT model (turbo)",
        "vae": "VAE encoder/decoder",
        "Qwen3-Embedding-0.6B": "Text encoder",
        "acestep-5Hz-lm-1.7B": "LM model (1.7B)",
    }

    results = {}
    all_ok = True
    for component, description in required_components.items():
        path = os.path.join(CHECKPOINTS_DIR, component)
        exists = os.path.isdir(path)
        # Check for weight files
        has_weights = False
        if exists:
            weight_names = [
                "model.safetensors",
                "model.safetensors.index.json",
                "diffusion_pytorch_model.safetensors",
                "diffusion_pytorch_model.safetensors.index.json",
            ]
            has_weights = any(
                os.path.isfile(os.path.join(path, w)) for w in weight_names
            )

        status = "OK" if has_weights else ("MISSING_WEIGHTS" if exists else "MISSING")
        if not has_weights:
            all_ok = False
        results[component] = status
        print(f"  {component} ({description}): {status}")

    print(f"\nModels: {'PASS' if all_ok else 'FAIL'}")
    return all_ok


def test_generation():
    """Test basic music generation."""
    print("\n" + "=" * 60)
    print("Step 3: Testing music generation...")
    print("=" * 60)

    try:
        # Add repo to path
        if REPO_DIR not in sys.path:
            sys.path.insert(0, REPO_DIR)

        from acestep.handler import AceStepHandler
        from acestep.inference import GenerationParams, GenerationConfig, generate_music

        # Initialize handler (DiT only, no LM for faster test)
        print("  Initializing DiT handler...")
        dit_handler = AceStepHandler()
        dit_handler.initialize_service(
            project_root=REPO_DIR,
            config_path="acestep-v15-turbo",
            device="cuda",
        )
        print("  DiT handler initialized.")

        # Simple generation without LM (faster)
        print("  Generating test audio (30s, no LM)...")
        params = GenerationParams(
            caption="A gentle piano melody with soft strings, ambient background music",
            duration=30,
            instrumental=True,
            inference_steps=8,
            seed=42,
        )

        config = GenerationConfig(
            batch_size=1,
            audio_format="wav",
        )

        start = time.time()
        result = generate_music(
            dit_handler,
            None,  # No LM handler
            params,
            config,
            save_dir=OUTPUT_DIR,
        )
        elapsed = time.time() - start

        if result.success:
            for audio in result.audios:
                print(f"  Generated: {audio['path']}")
                print(f"  Duration: {elapsed:.1f}s")
            print(f"\nGeneration: PASS")
            return True
        else:
            print(f"  Error: {result.error}")
            print(f"\nGeneration: FAIL")
            return False

    except Exception as e:
        print(f"  Exception: {e}")
        import traceback
        traceback.print_exc()
        print(f"\nGeneration: FAIL")
        return False


def main():
    print("ACE-Step 1.5 Test Script")
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    results = {}

    # Step 1: Test imports
    results["imports"] = test_imports()

    # Step 2: Test model checkpoints
    results["models"] = test_models_exist()

    # Step 3: Test generation (only if imports and models pass)
    if results["imports"] and results["models"]:
        results["generation"] = test_generation()
    else:
        results["generation"] = False
        print("\nSkipping generation test (prerequisites not met)")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for k, v in results.items():
        print(f"  {k}: {'PASS' if v else 'FAIL'}")

    all_pass = all(results.values())
    print(f"\nOverall: {'PASS' if all_pass else 'FAIL'}")

    if not all_pass:
        print("\nTroubleshooting:")
        if not results["imports"]:
            print("  - Install dependencies: bash /home/xsl/tools/ACE-Step-1.5/install_acestep.sh")
        if not results["models"]:
            print("  - Download models: huggingface-cli download ACE-Step/Ace-Step1.5 --local-dir /home/xsl/tools/ACE-Step-1.5/checkpoints")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
