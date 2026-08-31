from __future__ import annotations

"""Add a synthetic voice-over onto the user's own screen recording.

The user recorded real footage (dashboard + app.band.ai) but the mic captured
silence. This builds a clear TTS narration that explains ProcureGuard end to
end, paced to ride over the existing ~3:27 footage, then muxes it onto the
ORIGINAL video stream (keeping the user's real visuals, replacing the silent
audio track).

Narration is written in logical order and never claims exact on-screen timing,
so it stays correct regardless of precisely what frame is showing when.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "output" / "video_build"
SRC_VIDEO = Path(r"C:\Users\theih\Videos\Recording 2026-06-14 084729.mp4")
OUT = ROOT / "output" / "submission" / "procureguard-narrated-recording.mp4"

# One flowing narration. Paced to comfortably fit under ~207s of footage.
NARRATION = (
    "This is ProcureGuard A I, a multi-agent enterprise procurement system that "
    "runs on the real Band platform. "
    "Enterprise vendor approval is slow because it is fragmented. Procurement, "
    "finance, security, and legal each review in separate tools, and nobody sees "
    "the whole picture. ProcureGuard turns that into one coordinated decision "
    "room on Band. "
    "The case you are looking at is VectorCRM, a customer relationship tool that "
    "costs forty two thousand dollars, requested by Revenue Operations. The "
    "vendor wants access to customer contacts, opportunity notes, and email "
    "metadata, and integrates with Salesforce, HubSpot, and Slack. That data "
    "access is what makes this a real decision, not a rubber stamp. "
    "When the review runs, an Intake Coordinator opens a real Band room on app "
    "dot band dot a i and recruits four specialist agents by at-mention: Vendor "
    "Research, Finance R O I, Security Compliance, and Legal Policy. Each is a "
    "real routed message between agents. This is genuine Band coordination, not "
    "a simulator. You can see the real room, real messages, and real task "
    "events, every one carrying a Band issued identifier. "
    "The specialists review the request in parallel and hand their findings to "
    "an Evidence Clerk. Every finding is cited, tied back to a specific field in "
    "the original request, so there are no unsupported or hallucinated claims. "
    "The Evidence Clerk consolidates everything into one shared context packet "
    "with consensus points, unresolved questions, and a readiness score. "
    "Then comes the part most systems do not have. A Red Team Auditor challenges "
    "the conclusion before any approval, and it can issue a binding veto. In this "
    "run it found unresolved data protection gaps and vetoed, which "
    "deterministically forced the decision to escalate, even though the business "
    "case was reasonable. The system can overrule its own approval. That is a "
    "real safety control. "
    "The Approval Manager then synthesizes the entire review into a final "
    "decision, with an executive summary, conditions, and a risk register. A "
    "human procurement lead stays in control of the final call, with the exact "
    "signoffs required from the executive sponsor, legal, procurement, and "
    "security. "
    "Finally, the whole decision record is sealed with a SHA two fifty six hash, "
    "making the audit trail tamper evident. And the agents are genuinely cross "
    "framework, built on LangGraph, Crew A I, Pydantic A I, and Anthropic, all "
    "joining one Band room. That is Band's signature capability, coordinating "
    "agents across different runtimes, used for real. "
    "To summarize: ProcureGuard is eight cross framework agents collaborating on "
    "real Band, with cited evidence, an adversarial veto, a human gate, and a "
    "cryptographically sealed audit trail. It is not a report generator. It is a "
    "procurement decision court. Thank you for watching."
)


def synth_tts(text: str, wav_path: Path) -> None:
    ps = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$s.Rate = 0; $s.Volume = 100; "
        f"$s.SetOutputToWaveFile('{wav_path}'); "
        "$s.Speak([Console]::In.ReadToEnd()); $s.Dispose();"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        input=text, text=True, check=True,
    )


def duration_of(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def main() -> None:
    if not SRC_VIDEO.exists():
        print(f"MISSING SOURCE VIDEO: {SRC_VIDEO}", file=sys.stderr)
        sys.exit(1)
    BUILD.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)

    wav = BUILD / "vo_narration.wav"
    print("Synthesizing narration...")
    synth_tts(NARRATION, wav)

    vid_dur = duration_of(SRC_VIDEO)
    vo_dur = duration_of(wav)
    print(f"Video: {vid_dur:.1f}s | Narration: {vo_dur:.1f}s")
    if vo_dur > vid_dur:
        print("WARNING: narration longer than video; it will be cut at video end.", file=sys.stderr)

    # Keep the user's video stream as-is; replace audio with the narration.
    # -shortest is NOT used so the full video length is preserved.
    print(f"Muxing narration onto original footage -> {OUT}")
    subprocess.run(
        ["ffmpeg", "-y",
         "-i", str(SRC_VIDEO),
         "-i", str(wav),
         "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy",
         "-c:a", "aac", "-b:a", "192k",
         str(OUT)],
        check=True, capture_output=True,
    )
    out_dur = duration_of(OUT)
    print(f"DONE: {OUT} ({out_dur:.0f}s)")


if __name__ == "__main__":
    main()
