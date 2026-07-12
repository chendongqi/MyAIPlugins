#!/usr/bin/env python3
"""
Azure Speech Service TTS generator for daily tech podcast.

Parses [Alex]/[Sam] labeled dialogue script and generates a single
conversation-style audio file by sequentially concatenating per-turn audio.

Uses Microsoft Azure Cognitive Services Speech SDK (azure-cognitiveservices-speech).
Neural voices: zh-CN-YunxiNeural (Alex/male), zh-CN-XiaoxiaoNeural (Sam/female)
Output: Audio24Khz160KBitRateMonoMp3

Usage:
    python3 tts_azure.py <script_path> <output_path>

Environment variables (required):
    AZURE_SPEECH_KEY     - Azure Speech Service subscription key
    AZURE_SPEECH_REGION  - Azure region (e.g., eastasia, eastus, westeurope)

Install:
    pip install azure-cognitiveservices-speech pydub
    sudo apt install ffmpeg
"""

import argparse
import io
import os
import re
import sys
import tempfile

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

try:
    import azure.cognitiveservices.speech as speechsdk
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False


# ── Voice configuration ────────────────────────────────────────────────────

AZURE_VOICES = {
    "棋仔": "zh-CN-Yunhan:DragonHDFlashLatestNeural",    # 中文男声，理性分析师
    "依依": "zh-CN-Xiaoxiao2:DragonHDFlashLatestNeural", # 中文女声，情感连接者
}

# Azure SDK output format — 24kHz 160kbps 高保真 MP3
AZURE_OUTPUT_FORMAT = speechsdk.SpeechSynthesisOutputFormat.Audio24Khz160KBitRateMonoMp3 if SDK_AVAILABLE else None

# Silence gap between dialogue turns (ms)
PAUSE_BETWEEN_TURNS_MS = 450


# ── Script parser ──────────────────────────────────────────────────────────

def parse_script(script_path: str) -> list[dict]:
    """Parse [Alex]/[Sam] labeled dialogue into list of turns."""
    turns = []
    current_speaker = None
    current_lines = []

    with open(script_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            match = re.match(r"^\[([^\]]+)\]\s*(.*)", line)
            if match:
                if current_speaker and current_lines:
                    turns.append({
                        "speaker": current_speaker,
                        "text": " ".join(current_lines).strip(),
                    })
                current_speaker = match.group(1)
                text = match.group(2).strip()
                current_lines = [text] if text else []
            elif current_speaker:
                current_lines.append(line)

    if current_speaker and current_lines:
        turns.append({
            "speaker": current_speaker,
            "text": " ".join(current_lines).strip(),
        })

    # Replace [笑] with a natural pause comma; strip other stage directions
    cleaned = []
    for turn in turns:
        text = turn["text"]
        text = re.sub(r"\[笑\]", "，", text)
        text = re.sub(r"\[[^\]]+\]", "", text)
        text = text.strip()
        if text:
            cleaned.append({"speaker": turn["speaker"], "text": text})

    return cleaned


# ── Per-turn synthesis ────────────────────────────────────────────────────

def synthesize_turn(text: str, voice_name: str, api_key: str, region: str) -> bytes | None:
    """
    Synthesize one dialogue turn via Azure Speech SDK.
    Returns MP3 bytes on success, None on failure.

    Creates a fresh SpeechConfig + SpeechSynthesizer per call so that
    each turn can use a different voice without any shared state.
    """
    speech_config = speechsdk.SpeechConfig(subscription=api_key, region=region)
    speech_config.speech_synthesis_voice_name = voice_name
    speech_config.set_speech_synthesis_output_format(AZURE_OUTPUT_FORMAT)

    # Synthesize to in-memory stream (no file I/O)
    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=None,  # None = return audio data directly
    )

    result = synthesizer.speak_text_async(text).get()

    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return result.audio_data
    elif result.reason == speechsdk.ResultReason.Canceled:
        details = speechsdk.SpeechSynthesisCancellationDetails.from_result(result)
        print(f"    Canceled: {details.reason} — {details.error_details}")
        return None
    else:
        print(f"    Unexpected result reason: {result.reason}")
        return None


# ── Main generation logic ─────────────────────────────────────────────────

def generate_audio(turns: list[dict], output_path: str, api_key: str, region: str) -> bool:
    """
    Generate podcast audio:
    1. Synthesize each dialogue turn via Azure Speech SDK
    2. Concatenate segments sequentially with silence pauses (pydub)
    3. Export to MP3
    """
    combined = AudioSegment.empty()
    pause = AudioSegment.silent(duration=PAUSE_BETWEEN_TURNS_MS)

    print(f"Generating audio for {len(turns)} turns via Azure Speech SDK ({region})...")
    success_count = 0
    fail_count = 0

    for i, turn in enumerate(turns):
        speaker = turn["speaker"]
        text = turn["text"]
        voice_name = AZURE_VOICES.get(speaker, AZURE_VOICES["棋仔"])

        print(f"  [{i+1}/{len(turns)}] [{speaker}] {len(text)} chars → {voice_name}")

        audio_bytes = synthesize_turn(text, voice_name, api_key, region)

        if audio_bytes:
            try:
                seg = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
                combined = combined + seg + pause
                print(f"    OK: {len(seg) / 1000:.1f}s")
                success_count += 1
            except Exception as e:
                print(f"    ERROR decoding audio: {e}")
                fail_count += 1
        else:
            print(f"    SKIPPED (synthesis failed)")
            fail_count += 1

    if len(combined) == 0:
        print("ERROR: No audio segments generated")
        return False

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    combined.export(output_path, format="mp3", bitrate="160k")

    duration_min = len(combined) / 1000 / 60
    print(f"\nDone: {output_path}")
    print(f"  Duration: {duration_min:.1f} min")
    print(f"  Turns: {success_count} succeeded, {fail_count} failed")
    return True


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Azure Speech SDK TTS generator for tech podcast"
    )
    parser.add_argument("script", help="Podcast script file ([Alex]/[Sam] format)")
    parser.add_argument("output", help="Output MP3 file path")
    args = parser.parse_args()

    if not SDK_AVAILABLE:
        print("ERROR: azure-cognitiveservices-speech is required.")
        print("       Run: pip install azure-cognitiveservices-speech")
        sys.exit(1)

    if not PYDUB_AVAILABLE:
        print("ERROR: pydub is required. Run: pip install pydub")
        print("       Also ensure ffmpeg: sudo apt install ffmpeg")
        sys.exit(1)

    if not os.path.exists(args.script):
        print(f"ERROR: Script file not found: {args.script}")
        sys.exit(1)

    api_key = os.environ.get("AZURE_SPEECH_KEY")
    region = os.environ.get("AZURE_SPEECH_REGION")

    if not api_key:
        print("ERROR: AZURE_SPEECH_KEY not set")
        print("       Add to ~/.hermes/.env: AZURE_SPEECH_KEY=<your-key>")
        sys.exit(1)

    if not region:
        print("ERROR: AZURE_SPEECH_REGION not set")
        print("       Add to ~/.hermes/.env: AZURE_SPEECH_REGION=eastasia")
        sys.exit(1)

    turns = parse_script(args.script)
    if not turns:
        print("ERROR: No dialogue turns found. Check [Alex]/[Sam] markers in script.")
        sys.exit(1)

    print(f"Parsed {len(turns)} dialogue turns from {args.script}")
    speaker_counts: dict[str, int] = {}
    for t in turns:
        speaker_counts[t["speaker"]] = speaker_counts.get(t["speaker"], 0) + 1
    for sp, cnt in speaker_counts.items():
        print(f"  [{sp}]: {cnt} turns → voice: {AZURE_VOICES.get(sp, 'unknown')}")

    print(f"Azure region: {region} | Output format: Audio24Khz160KBitRateMonoMp3")

    success = generate_audio(turns, args.output, api_key, region)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
