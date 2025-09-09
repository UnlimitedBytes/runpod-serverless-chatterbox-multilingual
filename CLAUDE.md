# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a RunPod serverless packaging fork of **Chatterbox Multilingual TTS** by Resemble AI. The fork maintains identical model behavior while optimizing for cloud/serverless deployment on RunPod infrastructure. It provides zero-shot text-to-speech synthesis supporting 23 languages with emotion control and voice cloning capabilities.

## Core Architecture

### Main Components

**Handler System** (`handler.py:20-74`):
- RunPod serverless entry point using `runpod.serverless.start()`
- Loads ChatterboxTTS model on container initialization with device detection (CUDA/MPS/CPU)
- Processes JSON input with TTS parameters and returns base64-encoded WAV audio
- Handles all TTS parameters: text, audio_prompt_path, repetition_penalty, min_p, top_p, exaggeration, cfg_weight, temperature

**TTS Models** (`src/chatterbox/`):
- `ChatterboxTTS` (English-focused): Located in `tts.py`
- `ChatterboxMultilingualTTS` (23 languages): Located in `mtl_tts.py`
- Both models use T3 (0.5B Llama backbone), S3 tokenizer, and S3Gen vocoder
- Voice encoding through dedicated VoiceEncoder for zero-shot cloning

**Model Pipeline**:
1. **Text Processing**: Tokenization via EnTokenizer (English) or MTLTokenizer (multilingual)
2. **T3 Generation**: Llama-based text-to-semantic token generation
3. **S3 Vocoder**: Semantic tokens to audio waveform via S3Gen with HiFiGAN
4. **Voice Conditioning**: Optional audio prompt processing through VoiceEncoder for voice cloning

### Directory Structure

- `/src/chatterbox/`: Core TTS implementation
  - `/models/t3/`: Transformer-based text-to-semantic model 
  - `/models/s3gen/`: Semantic-to-audio generation
  - `/models/s3tokenizer/`: Audio tokenization
  - `/models/voice_encoder/`: Voice embedding for cloning
  - `/models/tokenizers/`: Text tokenizers (English/multilingual)
- `example_*.py`: Local testing scripts for TTS and voice conversion
- `gradio_*.py`: Interactive web interfaces for TTS and voice conversion
- `multilingual_app.py`: Gradio app specifically for multilingual TTS

## Development Commands

### Local Development
```bash
# Install dependencies
pip install chatterbox-tts runpod

# Test handler locally
python handler.py

# Run Gradio interfaces
python gradio_tts_app.py          # English TTS interface
python multilingual_app.py        # Multilingual TTS interface
python gradio_vc_app.py           # Voice conversion interface

# Basic TTS testing
python example_tts.py             # Tests both English and multilingual models
python example_vc.py              # Voice conversion example
```

### Docker/RunPod Deployment
```bash
# Build container
docker build -t chatterbox-runpod .

# Test locally with docker
docker run --gpus all -p 8000:8000 chatterbox-runpod

# RunPod testing
runpod test --config .runpod/tests.json
```

### Supported Languages (Multilingual Model)
Arabic (ar), Danish (da), German (de), Greek (el), English (en), Spanish (es), Finnish (fi), French (fr), Hebrew (he), Hindi (hi), Italian (it), Japanese (ja), Korean (ko), Malay (ms), Dutch (nl), Norwegian (no), Polish (pl), Portuguese (pt), Russian (ru), Swedish (sv), Swahili (sw), Turkish (tr), Chinese (zh)

## RunPod Configuration

**Test Suite** (`.runpod/tests.json`): Includes basic TTS, expressive speech, and long text generation tests with appropriate timeouts.

**Hub Configuration** (`.runpod/hub.json`): Configures RunPod marketplace listing with GPU requirements (ADA_48_PRO recommended, 10GB container disk).

## Key Parameters

**Core TTS Parameters**:
- `text`: Input text (required)
- `audio_prompt_path`: WAV file for voice cloning (optional)
- `exaggeration`: Emotion intensity (0.25-2.0, default 0.5)
- `cfg_weight`: Style fidelity vs clarity/pacing (0.0-1.0, default 0.5)
- `temperature`: Sampling randomness (0.05-5.0, default 0.8)
- `repetition_penalty`: Reduce repetition (1.0-2.0, default 1.2)
- `min_p`/`top_p`: Sampling parameters for diversity control

**Performance Tuning**:
- Expressive speech: Lower `cfg_weight` (~0.3) + higher `exaggeration` (≥0.7)
- Cross-language accent reduction: Set `cfg_weight = 0`
- Slow reference audio: Decrease `cfg_weight` to improve pacing

## Dependencies

Uses fixed versions for stability: torch 2.6.0, transformers 4.46.3, diffusers 0.29.0. Includes Perth watermarking for responsible AI usage. All models downloaded from Hugging Face hub (`ResembleAI/chatterbox`).

## Testing & Quality Assurance

When making changes:
1. Test basic TTS generation with `python example_tts.py`
2. Verify multilingual support if applicable
3. Run RunPod test suite: `runpod test --config .runpod/tests.json`
4. Validate container builds: `docker build -t test .`