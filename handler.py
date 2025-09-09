"""ChatterBox TTS RunPod Serverless Handler"""

import runpod
import torch
import torchaudio as ta
import base64
import io
from chatterbox.tts import ChatterboxTTS
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"

print(f"Using device: {device}")

# Load both models for optimal performance
print("Loading English TTS model...")
english_model = ChatterboxTTS.from_pretrained(device=device)

print("Loading Multilingual TTS model...")
multilingual_model = ChatterboxMultilingualTTS.from_pretrained(device=device)

print("Models loaded successfully!")

# Get supported languages
SUPPORTED_LANGUAGES = ChatterboxMultilingualTTS.get_supported_languages()


def handler(job):
    """Handler function that processes TTS requests."""
    try:
        job_input = job["input"]

        text = job_input.get("text")
        if not text:
            return {"error": "No text provided"}

        # Language selection with auto-detection
        language = job_input.get("language", "en")
        if language and language.lower() not in SUPPORTED_LANGUAGES:
            supported_langs = ", ".join(SUPPORTED_LANGUAGES.keys())
            return {
                "error": f"Unsupported language '{language}'. Supported languages: {supported_langs}"
            }

        # Core TTS parameters with Chatterbox defaults
        audio_prompt_path = job_input.get("audio_prompt_path", None)
        repetition_penalty = job_input.get("repetition_penalty", 1.2)  # English: 1.2, Multilingual: 2.0
        min_p = job_input.get("min_p", 0.05)
        top_p = job_input.get("top_p", 1.0)
        exaggeration = job_input.get("exaggeration", 0.5)
        cfg_weight = job_input.get("cfg_weight", 0.5)
        temperature = job_input.get("temperature", 0.8)
        return_format = job_input.get("return_format", "base64")

        # Select appropriate model based on language
        if language and language.lower() != "en":
            # Use multilingual model for non-English languages
            model = multilingual_model
            # Adjust default repetition penalty for multilingual model
            if job_input.get("repetition_penalty") is None:
                repetition_penalty = 2.0
            
            wav = model.generate(
                text=text,
                language_id=language.lower(),
                audio_prompt_path=audio_prompt_path,
                repetition_penalty=repetition_penalty,
                min_p=min_p,
                top_p=top_p,
                exaggeration=exaggeration,
                cfg_weight=cfg_weight,
                temperature=temperature,
            )
        else:
            # Use English model for English text
            model = english_model
            wav = model.generate(
                text=text,
                repetition_penalty=repetition_penalty,
                min_p=min_p,
                top_p=top_p,
                audio_prompt_path=audio_prompt_path,
                exaggeration=exaggeration,
                cfg_weight=cfg_weight,
                temperature=temperature,
            )

        buffer = io.BytesIO()
        ta.save(buffer, wav, model.sr, format="wav")
        buffer.seek(0)

        if return_format == "base64":
            # Encode audio as base64
            audio_base64 = base64.b64encode(buffer.read()).decode("utf-8")
            return {
                "audio_base64": audio_base64,
                "sample_rate": model.sr,
                "format": "wav",
                "language_used": language.lower() if language else "en",
                "model_used": "multilingual" if (language and language.lower() != "en") else "english"
            }
        else:
            return {
                "message": "URL format not implemented. Use base64.",
                "sample_rate": model.sr,
                "language_used": language.lower() if language else "en",
                "model_used": "multilingual" if (language and language.lower() != "en") else "english"
            }

    except Exception as e:
        return {"error": str(e)}

runpod.serverless.start({"handler": handler})