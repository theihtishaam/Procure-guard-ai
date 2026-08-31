from __future__ import annotations

"""Build a detailed narrated explainer MP4 from real captured dashboard frames.

Pipeline: per segment -> Windows TTS to WAV -> ffprobe duration -> render a
still-frame clip for that duration with the narration audio -> concat all clips.
Synthetic voice (Windows SAPI). Frames are real live-run captures.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "output" / "video_build"
FRAMES = BUILD / "frames"
OUT = ROOT / "output" / "submission" / "procureguard-detailed-explainer.mp4"

# Each segment: (frame filename, narration text)
SEGMENTS: list[tuple[str, str]] = [
    (
        "frame-01-top.png",
        "Welcome to ProcureGuard A I. This is a multi-agent enterprise procurement "
        "system that runs on the real Band platform. In the next few minutes I will "
        "walk you through a real vendor approval, from the input request all the way "
        "to a sealed, auditable decision. Everything you see here is from a real run.",
    ),
    (
        "frame-01-top.png",
        "Let us start with the input. The case is VectorCRM, a customer relationship "
        "tool that costs forty two thousand dollars. It was requested by Maya Patel in "
        "Revenue Operations. The important part for risk: this vendor wants access to "
        "customer contacts, opportunity notes, and email metadata, and it integrates "
        "with Salesforce, HubSpot, and Slack. That data access is what makes approval "
        "a real decision, not a rubber stamp.",
    ),
    (
        "frame-02-bandproof.png",
        "When the review runs, the first thing to prove is that this is genuinely Band. "
        "This panel shows the live Band room. We have a real room I D on app dot band "
        "dot a i, ten real Band messages, and seven task events. Every one of these "
        "carries a Band issued identifier. The agents are not pretending to talk in a "
        "simulator. They are coordinating through the actual Band platform.",
    ),
    (
        "frame-03-handoff.png",
        "Here is the coordination handoff map. An Intake Coordinator opens the room and "
        "recruits four specialist agents by at-mention: Vendor Research, Finance R O I, "
        "Security Compliance, and Legal Policy. Each arrow is a real routed message "
        "between agents. The specialists review the case in parallel, then hand their "
        "findings to an Evidence Clerk who consolidates everything.",
    ),
    (
        "frame-04-taskstate.png",
        "This is the task state and recruitment board. It shows who owns each piece of "
        "work, the current status, and the evidence each agent produced. This is what "
        "makes the collaboration auditable. You can see coordinated work with clear "
        "ownership, not just a chat log.",
    ),
    (
        "frame-07-citations.png",
        "Now the part that makes the findings trustworthy. Each specialist artifact "
        "carries cited evidence. Every finding is tied back to a specific field in the "
        "original request. For example, a finance claim about the forty two thousand "
        "dollar spend is linked directly to the requested amount field. There are no "
        "unsupported or hallucinated claims. Everything traces to the source.",
    ),
    (
        "frame-05-context.png",
        "The Evidence Clerk produces one shared context packet. It captures the points "
        "the agents agree on, the unresolved questions that still need answers, and a "
        "readiness score. This single packet becomes the shared source of truth that "
        "the rest of the room works from.",
    ),
    (
        "frame-06-veto.png",
        "This is the differentiator most systems do not have. A Red Team Auditor "
        "challenges the conclusion before any approval. It can issue a binding veto. "
        "In this run it found unresolved data protection gaps and issued a veto. That "
        "veto deterministically forced the decision to escalate, even though the "
        "business case was reasonable. The system can overrule its own approval. This "
        "is a real safety control, not a formality.",
    ),
    (
        "frame-08-decision.png",
        "The Approval Manager then synthesizes everything into a final decision. Here "
        "the decision is escalate, because the red team did not clear the packet. It "
        "comes with a clear executive summary, conditions, and a risk register. The "
        "decision is a reasoned synthesis of the entire review, not a single opinion.",
    ),
    (
        "frame-09-humangate.png",
        "A human stays in control of the final call. The human approval gate shows the "
        "gate status and the exact signoffs required, here from the executive sponsor, "
        "legal, procurement, and security. The agents prepare the decision and the "
        "evidence, but a person makes the final approval. That is human in the loop by "
        "design.",
    ),
    (
        "frame-10-auditseal.png",
        "Finally, the entire decision record is sealed with a S H A two fifty six hash. "
        "This makes the audit trail tamper evident. The panel also shows the agent "
        "framework profile. The agents are genuinely cross framework, built on "
        "LangGraph, Crew A I, Pydantic A I, and Anthropic, all joining one Band room. "
        "That is Band's signature capability, coordinating agents across different "
        "runtimes, and we use it for real.",
    ),
    (
        "frame-11-timeline.png",
        "And here is the full Band room timeline, the complete record of every message "
        "and event the agents exchanged. To summarize: ProcureGuard is eight cross "
        "framework agents collaborating on real Band, with cited evidence, an "
        "adversarial veto, a human gate, and a cryptographically sealed audit trail. "
        "It is not a report generator. It is a procurement decision court. Thank you "
        "for watching.",
    ),
]


def synth_tts(text: str, wav_path: Path) -> None:
    ps = (
        "Add-Type -AssemblyName System.Speech; "
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
        "$s.Rate = 0; $s.Volume = 100; "
        f"$s.SetOutputToWaveFile('{wav_path}'); "
        f"$s.Speak([Console]::In.ReadToEnd()); $s.Dispose();"
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
    FRAMES.mkdir(parents=True, exist_ok=True)
    clips: list[Path] = []
    concat_lines: list[str] = []

    for i, (frame, text) in enumerate(SEGMENTS):
        frame_path = FRAMES / frame
        if not frame_path.exists():
            print(f"MISSING FRAME: {frame_path}", file=sys.stderr)
            sys.exit(1)
        wav = BUILD / f"d_seg{i:02d}.wav"
        clip = BUILD / f"d_seg{i:02d}.mp4"
        print(f"[{i+1}/{len(SEGMENTS)}] TTS -> {wav.name}")
        synth_tts(text, wav)
        dur = duration_of(wav) + 0.7  # small tail pad
        print(f"    {dur:.1f}s -> {clip.name} ({frame})")
        subprocess.run(
            ["ffmpeg", "-y", "-loop", "1", "-i", str(frame_path), "-i", str(wav),
             "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
             "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,"
                    "pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=white",
             "-c:a", "aac", "-b:a", "160k", "-shortest", "-t", f"{dur:.2f}",
             str(clip)],
            check=True, capture_output=True,
        )
        clips.append(clip)
        concat_lines.append(f"file '{clip.as_posix()}'")

    concat_file = BUILD / "d_concat.txt"
    concat_file.write_text("\n".join(concat_lines), encoding="utf-8")
    print(f"Concatenating {len(clips)} clips -> {OUT}")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
         str(OUT)],
        check=True, capture_output=True,
    )
    total = duration_of(OUT)
    print(f"DONE: {OUT} ({total:.0f}s)")


if __name__ == "__main__":
    main()
