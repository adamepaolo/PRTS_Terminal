from . import gemini, mistral, ollama

DEFAULT_MODELS = {
    "gemini": gemini.DEFAULT_MODEL,
    "mistral": mistral.DEFAULT_MODEL,
    "ollama": ollama.DEFAULT_MODEL,
}

BACKENDS = {
    "gemini": gemini.call,
    "mistral": mistral.call,
    "ollama": ollama.call,
}

__all__ = ["BACKENDS", "DEFAULT_MODELS"]
