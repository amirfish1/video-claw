#!/usr/bin/env python3
"""Reveal sub-bass drone — fills the empty-room reveal so it doesn't feel hollow
(user: "feels empty... maybe the bass sound... especially the transition into the
empty rooms, but throughout too"). A deep cinematic sub bed: layered low sines with a
swell INTO the turn, a sustained body, subtle air, and a soft tail. ~13s to sit under
the 26-38s reveal. Output: review-room/v2.10/assets/reveal_bass.wav
"""
import subprocess
from pathlib import Path

A = Path(__file__).resolve().parents[2] / "review-room" / "v2.10" / "assets"
OUT = A / "reveal_bass.wav"
FF = __import__("imageio_ffmpeg").get_ffmpeg_exe()
DUR = 13.0


def main():
    # three low sines (sub body + a little harmonic), filtered noise for air,
    # a 1.8s swell-in at the transition, gentle tremolo movement, soft tail.
    fc = (
        f"sine=frequency=38:duration={DUR}[s1];"
        f"sine=frequency=50:duration={DUR}[s2];"
        f"sine=frequency=76:duration={DUR}[s3];"
        f"anoisesrc=d={DUR}:c=pink:a=0.06[n];"
        f"[s1]volume=0.9[a1];[s2]volume=0.55[a2];[s3]volume=0.22[a3];"
        f"[n]lowpass=f=180,volume=0.5[air];"
        f"[a1][a2][a3][air]amix=inputs=4:normalize=0[mix];"
        # slow tremolo movement + keep it sub + swell in + soft tail
        f"[mix]tremolo=f=0.25:d=0.3,lowpass=f=200,"
        f"afade=t=in:st=0:d=1.8:curve=ipar,afade=t=out:st={DUR-1.5}:d=1.5,"
        f"volume=1.4,alimiter=limit=0.9[out]"
    )
    subprocess.run([FF, "-y", "-filter_complex", fc, "-map", "[out]",
                    "-ar", "48000", "-ac", "2", "-t", str(DUR), str(OUT)], check=True)
    print("wrote", OUT, f"({DUR}s)")


if __name__ == "__main__":
    main()
