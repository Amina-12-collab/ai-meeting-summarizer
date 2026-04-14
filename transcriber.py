"""
Module 2: Speech-to-Text Transcription
Uses OpenAI Whisper (local, free) as the primary transcription engine.
Falls back to a stub if whisper is not installed, so the app still runs.
"""
 
import os
 
 
def transcribe_audio(file_path: str) -> str:
    """
    Transcribe an audio file to text using OpenAI Whisper.
 
    Args:
        file_path: Absolute path to the saved audio file.
 
    Returns:
        Plain-text transcript string.
 
    Raises:
        RuntimeError: If whisper is not available or transcription fails.
    """
    try:
        import whisper
    except ImportError:
        raise RuntimeError(
            "OpenAI Whisper is not installed.\n"
            "Install it with:  pip install openai-whisper\n"
            "Also requires ffmpeg:  brew install ffmpeg  /  apt install ffmpeg"
        )
 
    # Load the smallest model that gives good accuracy.
    # Options (speed vs accuracy): tiny, base, small, medium, large
    # Change to "small" or "medium" for better results on noisy audio.
    model_name = os.getenv("WHISPER_MODEL", "base")
 
    try:
        model = whisper.load_model(model_name)
        result = model.transcribe(file_path, fp16=False)
        return result["text"].strip()
    except Exception as e:
        raise RuntimeError(f"Whisper transcription error: {e}")