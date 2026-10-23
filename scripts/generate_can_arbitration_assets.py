"""Deterministically rasterize the CAN arbitration technical diagrams."""

from __future__ import annotations

import hashlib
from pathlib import Path

import cairosvg


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/can_arbitration_illustrations/source"
OUTPUT = ROOT / "assets/can_arbitration_illustrations"
BG = "#F4F6F8"
NAVY = "#16324F"
BLUE = "#2D6CDF"
RED = "#D95D39"
GREEN = "#2A9D8F"
GRAY = "#5C677D"
GOLD = "#F2C14E"


def svg(title: str, subtitle: str, body: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1672" height="941" viewBox="0 0 1672 941">
<rect width="1672" height="941" fill="{BG}"/>
<rect x="55" y="45" width="1562" height="851" rx="28" fill="none" stroke="{NAVY}" stroke-width="4"/>
<text x="95" y="120" font-family="Arial" font-size="52" font-weight="700" fill="{NAVY}">{title}</text>
<text x="98" y="175" font-family="Arial" font-size="28" fill="{GRAY}">{subtitle}</text>
{body}
</svg>'''


def write(name: str, content: str) -> None:
    SOURCE.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    source = SOURCE / f"{name}.svg"
    output = OUTPUT / f"{name}.png"
    source.write_text(content, encoding="utf-8")
    cairosvg.svg2png(bytestring=content.encode("utf-8"), write_to=str(output), output_width=1672, output_height=941)


def bit_boxes(y: int, bits: str, color: str) -> str:
    parts = []
    x = 520
    for bit in bits.split():
        fill = color if bit == "0" else "#FFFFFF"
        text_fill = "#FFFFFF" if bit == "0" else color
        parts.append(f'<rect x="{x}" y="{y}" width="70" height="70" rx="8" fill="{fill}" stroke="{color}" stroke-width="3"/><text x="{x + 25}" y="{y + 48}" font-family="Arial" font-size="38" fill="{text_fill}">{bit}</text>')
        x += 78
    return "".join(parts)


def id_boxes(y: int, bits: str, color: str) -> str:
    parts = []
    x = 300
    for bit in bits.split():
        fill = color if bit == "0" else "#FFFFFF"
        text_fill = "#FFFFFF" if bit == "0" else color
        parts.append(f'<rect x="{x}" y="{y}" width="110" height="90" rx="10" fill="{fill}" stroke="{color}" stroke-width="4"/><text x="{x + 38}" y="{y + 58}" font-family="Arial" font-size="38" fill="{text_fill}">{bit}</text>')
        x += 200
    return "".join(parts)


def main() -> int:
    write("01-dominant-recessive", svg("CAN BUS STATES", "Dominant overwrites recessive on the shared bus", f'''
<text x="110" y="285" font-family="Arial" font-size="38" fill="{BLUE}">Node A sends 1</text>
<text x="110" y="505" font-family="Arial" font-size="38" fill="{RED}">Node B sends 0</text>
<line x1="420" y1="320" x2="1450" y2="320" stroke="{BLUE}" stroke-width="12"/>
<line x1="420" y1="540" x2="1450" y2="540" stroke="{RED}" stroke-width="12"/>
<text x="760" y="270" font-family="Arial" font-size="28" fill="{BLUE}">RECESSIVE</text>
<text x="760" y="490" font-family="Arial" font-size="28" fill="{RED}">DOMINANT</text>
<line x1="420" y1="640" x2="1450" y2="640" stroke="{NAVY}" stroke-width="20"/>
<text x="720" y="705" font-family="Arial" font-size="38" fill="{NAVY}">BUS = DOMINANT 0</text>'''))
    write("02-two-node-bits", svg("BITWISE ARBITRATION", "Every transmitter monitors the bus while it sends", f'''
<text x="110" y="270" font-family="Arial" font-size="38" fill="{BLUE}">Node A ID 0x120</text>
<text x="110" y="430" font-family="Arial" font-size="38" fill="{RED}">Node B ID 0x320</text>
{bit_boxes(300, '0 0 1 0 0 0 0 0 0 0 0', BLUE)}
{bit_boxes(460, '0 1 1 0 0 0 0 0 0 0 0', RED)}
<line x1="520" y1="710" x2="1450" y2="710" stroke="{GOLD}" stroke-width="18"/>
<text x="610" y="700" font-family="Arial" font-size="28" fill="{NAVY}">TX=1, BUS=0 → Node B stops</text>
<text x="140" y="390" font-family="Arial" font-size="28" fill="{GRAY}">send + sample</text>
<text x="140" y="550" font-family="Arial" font-size="28" fill="{GRAY}">send + sample</text>'''))
    write("03-id-compare", svg("IDENTIFIER COMPARISON", "Lower numeric ID reaches dominant first", f'''
<text x="150" y="270" font-family="Arial" font-size="38" fill="{NAVY}">bit</text>
<text x="320" y="270" font-family="Arial" font-size="38" fill="{NAVY}">10</text><text x="520" y="270" font-family="Arial" font-size="38" fill="{NAVY}">9</text><text x="720" y="270" font-family="Arial" font-size="38" fill="{NAVY}">8</text><text x="920" y="270" font-family="Arial" font-size="38" fill="{NAVY}">7</text>
<text x="150" y="400" font-family="Arial" font-size="38" fill="{BLUE}">0x120</text><text x="150" y="550" font-family="Arial" font-size="38" fill="{RED}">0x320</text>
{id_boxes(330, '0 0 1 0', BLUE)}
{id_boxes(480, '0 1 1 0', RED)}
<text x="1080" y="400" font-family="Arial" font-size="28" fill="{BLUE}">dominant</text><text x="1080" y="550" font-family="Arial" font-size="28" fill="{RED}">recessive</text>
<text x="180" y="720" font-family="Arial" font-size="38" fill="{NAVY}">At bit 9: 0 wins over 1 → 0x120 keeps transmitting</text>'''))
    write("04-loser-stops", svg("NON-DESTRUCTIVE RESULT", "Loser stops; winner continues without a collision", f'''
<text x="130" y="285" font-family="Arial" font-size="28" fill="{GRAY}">time →</text><line x1="350" y1="325" x2="1450" y2="325" stroke="{NAVY}" stroke-width="4"/>
<text x="120" y="445" font-family="Arial" font-size="38" fill="{BLUE}">Node A</text><line x1="350" y1="460" x2="850" y2="460" stroke="{BLUE}" stroke-width="18"/><text x="600" y="385" font-family="Arial" font-size="28" fill="{GREEN}">wins</text><line x1="850" y1="460" x2="1450" y2="460" stroke="{GREEN}" stroke-width="18"/>
<text x="120" y="610" font-family="Arial" font-size="38" fill="{RED}">Node B</text><line x1="350" y1="625" x2="850" y2="625" stroke="{RED}" stroke-width="18"/><text x="720" y="690" font-family="Arial" font-size="28" fill="{RED}">loses arbitration</text><line x1="850" y1="625" x2="1450" y2="625" stroke="#BBBBBB" stroke-width="8"/>
<line x1="850" y1="250" x2="850" y2="730" stroke="{GOLD}" stroke-width="5"/><text x="900" y="735" font-family="Arial" font-size="28" fill="{NAVY}">header decision point</text>'''))
    write("05-checklist", svg("CAN ARBITRATION CHECK", "A reproducible five-step explanation", f'''
<text x="270" y="250" font-family="Arial" font-size="38" fill="{NAVY}">dominant beats recessive</text>
<text x="270" y="340" font-family="Arial" font-size="38" fill="{NAVY}">nodes compare identifier bits</text>
<text x="270" y="430" font-family="Arial" font-size="38" fill="{NAVY}">recessive + dominant = loss</text>
<text x="270" y="520" font-family="Arial" font-size="38" fill="{NAVY}">loser stops transmitting</text>
<text x="270" y="610" font-family="Arial" font-size="38" fill="{NAVY}">winner frame remains intact</text>
<text x="970" y="720" font-family="Arial" font-size="38" fill="{RED}">priority = lower ID</text>'''))
    print("can_assets_generated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
