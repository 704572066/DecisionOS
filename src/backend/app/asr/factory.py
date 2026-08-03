from app.asr.base import StreamingAsrProvider
from app.asr.deepgram_provider import DeepgramStreamingAsrProvider


def create_streaming_provider(provider_name: str) -> StreamingAsrProvider:
    name = provider_name.strip().lower()
    if name == "deepgram":
        return DeepgramStreamingAsrProvider()
    raise ValueError(f"不支持的流式 ASR Provider: {provider_name}")
