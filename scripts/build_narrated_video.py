from __future__ import annotations

"""Build a narrated explainer MP4 from dashboard screenshots + Windows TTS.

Pipeline:
  1. Define segments: (screenshot, narration text).
  2. Synthesize a voice-over WAV per segment via Windows System.Speech (PowerShell).
  3. Measure each WAV duration with ffprobe.
  4. Render one MP4 clip per segment (image held for the audio duration, 1280x720).
  5. Concatenate all clips into output/submission/procureguard-explainer.mp4.

The voice is a synthetic Windows TTS voice (no human narration available here).
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / "output" / "playwright"
SUB = ROOT / "output" / "submission"
BUILD = ROOT / "output" / "video_build"
BUILD.mkdir(parents=True, exist_ok=True)

# Each segment: (image path, narration). Images chosen to match what is described.
SEGMENTS: list[tuple[Path, str]] = [
    (
        SUB / "procureguard-cover.png",
        "ProcureGuard A I. A live, multi-agent enterprise procurement decision room, "
        "built on Band. Let me walk you through what it does and how it works.",
    ),
    (
        SHOTS / "procureguard-live-dashboard.png",
        "Enterprise vendor approval is slow because it is fragmented. Procurement, finance, "
        "security, and legal each review in separate tools, and nobody sees the whole picture. "
        "ProcureGuard turns that into one coordinated decision room. Here is a real case: "
        "VectorCRM, a forty-two thousand dollar customer-data tool, requested by Revenue Operations.",
    ),
    (
        SHOTS / "procureguard-live-band-proof.png",
        "This is the most important part. The workflow runs on the real Band platform, not a "
        "simulator. This panel shows the live Band room, with ten real Band messages and seven "
        "task events, each carrying a Band-issued identifier. Eight agents collaborate here through "
        "real at-mention message routing.",
    ),
    (
        SHOTS / "procureguard-handoff-map-final.png",
        "An Intake Coordinator opens the room and recruits its specialist peers: Vendor Research, "
        "Finance R O I, Security Compliance, and Legal Policy. They review in parallel, then hand "
        "their findings to an Evidence Clerk. This map shows every routed handoff between agents.",
    ),
    (
        SHOTS / "procureguard-task-state-final.png",
        "Every task has an owner, a status, and evidence. This is coordinated work with a clear "
        "audit trail, not just a chat transcript. You can see exactly who did what, and when.",
    ),
    (
        SHOTS / "procureguard-dashboard-final.png",
        "What makes the findings trustworthy is that every claim is cited, tied back to a specific "
        "field in the request, so there are no hallucinated conclusions. The Evidence Clerk then "
        "consolidates everything into one shared context packet.",
    ),
    (
        SHOTS / "procureguard-impact-controls-final.png",
        "Then comes the part most systems do not have. A Red Team Auditor challenges the conclusion "
        "before approval, and can issue a binding veto. Here it found unresolved data-protection gaps, "
        "so it vetoed, and that deterministically forced the decision to escalate, even though the "
        "business case was strong. The system can overrule its own approval. That is a safety control, "
        "not a rubber stamp.",
    ),
    (
        SHOTS / "procureguard-band-proof-panel.png",
        "The Approval Manager synthesizes everything into a final decision and routes it to a human "
        "procurement lead with the exact signoffs required. A human stays in control of the final call. "
        "The entire record is sealed with a SHA-256 hash, making it tamper-evident, and can be downloaded "
        "as a full report and evidence bundle.",
    ),
    (
        SHOTS / "procureguard-live-dashboard.png",
        "And the agents are genuinely cross-framework: LangGraph, CrewAI, Pydantic A I, and Anthropic, "
        "all joining one Band room. That is Band's signature capability, coordinating agents across "
        "different runtimes. ProcureGuard is not a report generator. It is a procurement decision court. "
        "Thank you for watching.",
    ),
]


def synth_tts(text: str, wav_path: Path) -> None:
    """Generate a WAV from text using Windows System.Speech via PowerShell."""
    txt_path = wav_path.with_suffix(".txt")
    txt_path.write_text(text, encoding="utf-8")
    ps = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$s.Rate = 0; $s.Volume = 100; "
        f"$s.SetOutputToWaveFile('{wav_path}'); "
        f"$t = [System.IO.File]::ReadAllText('{txt_path}'); "
        "$s.Speak($t); $s.Dispose();"
    )
    subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps],
        check=True,
        capture_output=True,
        text=True,
    )


def wav_duration(wav_path: Path) -> float:
    out = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(wav_path),
        ],
        check=True, capture_output=True, text=True,
    )
    return float(out.stdout.strip())


def build_clip(image: Path, wav: Path, duration: float, out_mp4: Path) -> None:
    # Pad duration slightly so narration is not cut off; add 0.6s tail.
    dur = duration + 0.6
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(image),
            "-i", str(wav),
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=white",
            "-c:a", "aac", "-b:a", "192k",
            "-t", f"{dur:.2f}",
            "-shortest", str(out_mp4),
        ],
        check=True, capture_output=True, text=True,
    )


def main() -> None:
    clips: list[Path] = []
    for i, (image, text) in enumerate(SEGMENTS):
        if not image.exists():
            raise SystemExit(f"Missing screenshot: {image}")
        wav = BUILD / f"seg{i:02d}.wav"
        clip = BUILD / f"seg{i:02d}.mp4"
        print(f"[{i+1}/{len(SEGMENTS)}] TTS -> {wav.name}")
        synth_tts(text, wav)
        dur = wav_duration(wav)
        print(f"    duration {dur:.1f}s, rendering {clip.name}")
        build_clip(image, wav, dur, clip)
        clips.append(clip)

    concat_list = BUILD / "concat.txt"
    concat_list.write_text("".join(f"file '{c.as_posix()}'\n" for c in clips), encoding="utf-8")
    out = SUB / "procureguard-explainer.mp4"
    print(f"Concatenating {len(clips)} clips -> {out}")
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
            str(out),
        ],
        check=True, capture_output=True, text=True,
    )
    total = wav_duration(out)
    print(f"DONE: {out} ({total:.0f}s)")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print("FFmpeg/TTS error:", exc.stderr[-800:] if exc.stderr else exc, file=sys.stderr)
        raise
