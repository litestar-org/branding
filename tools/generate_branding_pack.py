"""Generate the complete 22-project Ecosystem Branding Pack and inline README banners."""

from dataclasses import dataclass
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
BRANDING_OUT_DIR = REPO_ROOT / "assets" / "projects"
LEGACY_SVG_TRANSPARENT_DIR = REPO_ROOT / "assets" / "Branding - SVG - Transparent"
LEGACY_PNG_TRANSPARENT_DIR = REPO_ROOT / "assets" / "Branding - PNG - Transparent"

GOLD = "#EDB641"
NAVY = "#202235"
WHITE = "#FFFFFF"
LIGHT_BG = "#F8FAFC"
SLATE_BORDER = "#CBD5E1"
LEGACY_SUB_LIGHT = "#737373"
CANVAS_SIZE = 256
FFMPEG_BIN = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"

_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")
_TRANSLATE_PATH_RE = re.compile(
    r'<g transform="translate\(([^,]+),\s*([^)]+)\)">(?:<g><path d="([^"]+)"/></g>|<g/>)</g>'
)

_OPTICAL_KERNING: dict[tuple[str, str], float] = {
    ("V", "A"): -0.35,
    ("A", "V"): -0.35,
    ("A", "Y"): -0.35,
    ("Y", "A"): -0.35,
    ("A", "T"): -0.25,
    ("T", "A"): -0.25,
    ("T", "Y"): -0.30,
    ("Y", "P"): -0.20,
    ("L", "T"): -0.30,
    ("L", "Y"): -0.35,
    ("L", "V"): -0.30,
    ("P", "A"): -0.25,
    ("F", "A"): -0.25,
}


@dataclass(frozen=True, slots=True)
class VectorFont:
    """Extracted vector path outlines for uppercase and regular brand typography."""

    bold_upper: dict[str, str]
    regular_upper: dict[str, str]
    litestar_star_dark: str
    litestar_star_light: str
    litestar_header_dark: str
    litestar_header_light: str
    litestar_badge_paths: tuple[str, ...]

    @classmethod
    def load_from_repo(cls, repo_root: Path) -> "VectorFont":
        """Extract Inter Bold and Regular vector glyph tables and official badge paths from existing brand SVGs."""
        guidelines_text = (repo_root / "assets" / "Litestar Brand Guidelines.svg").read_text(encoding="utf-8")
        raw_matches = re.findall(
            r'<g transform="translate\(([^,]+),\s*([^)]+)\)">\s*<g>\s*<path d="([^"]+)"', guidelines_text
        )
        upper_row = [(float(x), d) for x, y, d in raw_matches if abs(float(y) - 617.23) < 0.15]
        bold_upper = {ch: d for ch, (_, d) in zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", upper_row[:26], strict=True)}

        svg_dir = repo_root / "assets" / "Branding - SVG - Transparent"
        words_by_file = {
            "AA - Banner - Inline - Dark.svg": "ADVANCED ALCHEMY",
            "OracleDB - Banner - Inline - Dark.svg": "ORACLE DB",
            "Organization Project - Banner - Inline - Dark.svg": "AN OFFICIAL ORG PROJECT",
            "Polyfactory - Banner - Inline - Dark.svg": "POLYFACTORY",
            "Fullstack - Banner - Inline - Dark.svg": "FULLSTACK",
            "Awesome - Banner - Inline - Dark.svg": "AWESOME",
            "SAQ - Banner - Inline - Dark.svg": "SAQ",
            "Vite - Banner - Inline - Dark.svg": "VITE",
            "Type Lens - Banner - Inline - Dark.svg": "TYPE LENS",
        }
        regular_upper: dict[str, str] = {}
        for fname, text in words_by_file.items():
            svg_content = (svg_dir / fname).read_text(encoding="utf-8")
            items = _TRANSLATE_PATH_RE.findall(svg_content)
            if fname == "Organization Project - Banner - Inline - Dark.svg":
                top = [(float(x), float(y), d) for x, y, d in items if float(y) < 100]
                bot = [(float(x), float(y), d) for x, y, d in items if float(y) > 200]
                selected = top + [(0.0, 0.0, "")] + bot
            else:
                selected = [(float(x), float(y), d) for x, y, d in items if float(y) > 200]
            for ch, (_, _, d) in zip(text, selected, strict=True):
                if ch != " " and d:
                    regular_upper[ch] = d

        regular_upper["X"] = (
            "M 1.09375 -31.140625 L 5.40625 -31.140625 L 14.234375 -18.25 "
            "L 23.0625 -31.140625 L 27.375 -31.140625 L 16.40625 -15.5625 "
            "L 27.375 0 L 23.0625 0 L 14.234375 -12.875 L 5.40625 0 "
            "L 1.09375 0 L 12.0625 -15.5625 Z M 1.09375 -31.140625 "
        )
        regular_upper["Z"] = (
            "M 2.34375 0 L 2.34375 -3.046875 L 19.890625 -27.796875 "
            "L 2.34375 -27.796875 L 2.34375 -31.140625 L 24.421875 -31.140625 "
            "L 24.421875 -28.09375 L 6.875 -3.34375 L 24.421875 -3.34375 "
            "L 24.421875 0 Z M 2.34375 0 "
        )

        saq_dark = (svg_dir / "SAQ - Banner - Inline - Dark.svg").read_text(encoding="utf-8")
        saq_light = (svg_dir / "SAQ - Banner - Inline - Light.svg").read_text(encoding="utf-8")

        star_dark_end = saq_dark.index('<g fill="#ffffff" fill-opacity="1"><g transform="translate(543.544883')
        star_dark_start = saq_dark.index("<defs>")
        litestar_star_dark = saq_dark[star_dark_start:star_dark_end]

        sub_dark_start = saq_dark.index('<g fill="#ffffff" fill-opacity="1"><g transform="translate(740.194014')
        litestar_header_dark = saq_dark[star_dark_end:sub_dark_start]

        star_light_end = saq_light.index('<g fill="#202235" fill-opacity="1"><g transform="translate(543.688742')
        star_light_start = saq_light.index("<defs>")
        litestar_star_light = saq_light[star_light_start:star_light_end]

        sub_light_start = saq_light.index('<g fill="#737373" fill-opacity="1"><g transform="translate(740.055947')
        litestar_header_light = saq_light[star_light_end:sub_light_start]

        badge_svg = (svg_dir / "Badge - Blue and Yellow.svg").read_text(encoding="utf-8")
        raw_badge_paths = tuple(re.findall(r'<path fill="#edb641" d="([^"]+)"', badge_svg))

        return cls(
            bold_upper=bold_upper,
            regular_upper=regular_upper,
            litestar_star_dark=litestar_star_dark,
            litestar_star_light=litestar_star_light,
            litestar_header_dark=litestar_header_dark,
            litestar_header_light=litestar_header_light,
            litestar_badge_paths=raw_badge_paths,
        )

    def measure_bold(
        self, text: str, cap_height: float, tracking: float, space_width: float
    ) -> tuple[float, list[tuple[float, str]]]:
        """Measure and position an uppercase string using Inter Bold vector paths."""
        factor = cap_height / 5.8125
        items: list[tuple[float, str]] = []
        cursor = 0.0
        clean = text.upper()
        for idx, ch in enumerate(clean):
            if ch == " ":
                cursor += space_width
                continue
            if ch == "-":
                bar_w = cap_height * 0.42
                bar_h = cap_height * 0.16
                bar_y = -cap_height * 0.42
                sd = f"M 0 {bar_y:.2f} L {bar_w:.2f} {bar_y:.2f} L {bar_w:.2f} {bar_y - bar_h:.2f} L 0 {bar_y - bar_h:.2f} Z"
                items.append((cursor, sd))
                cursor += bar_w + (tracking if idx < len(clean) - 1 and clean[idx + 1] != " " else 0.0)
                continue
            raw_d = self.bold_upper[ch]
            nums = [float(n) * factor for n in _NUMBER_RE.findall(raw_d)]
            xs = nums[0::2]
            min_x, max_x = min(xs), max(xs)
            scaled_d = _NUMBER_RE.sub(lambda m: f"{float(m.group(0)) * factor:.4f}", raw_d)
            items.append((cursor - min_x, scaled_d))
            advance = max_x - min_x
            if idx < len(clean) - 1 and clean[idx + 1] != " ":
                kern = _OPTICAL_KERNING.get((ch, clean[idx + 1]), 0.0) * tracking
                advance += tracking + kern
            cursor += advance
        return cursor, items

    def render_bold_header(self, text: str, start_x: float, baseline_y: float, fill: str) -> tuple[float, str]:
        """Render a top-tier Inter Bold header matching the 64.08px cap height of original Litestar inline banners."""
        total_w, items = self.measure_bold(text, cap_height=64.08, tracking=16.5, space_width=28.0)
        parts = [f'<g fill="{fill}" fill-opacity="1">']
        for gx, sd in items:
            parts.append(f'<g transform="translate({start_x + gx:.6f}, {baseline_y:.6f})"><g><path d="{sd}"/></g></g>')
        parts.append("</g>")
        return start_x + total_w / 2.0, "".join(parts)

    def render_regular_centered(self, text: str, center_x: float, baseline_y: float, fill: str) -> str:
        """Render an uppercase string in the legacy 31.14px Regular subtitle style centered at center_x."""
        clean = text.upper()
        tracking = 12.2
        space_width = 22.0
        items: list[tuple[float, str]] = []
        cursor = 0.0
        for idx, ch in enumerate(clean):
            if ch == " ":
                items.append((cursor, ""))
                cursor += space_width + tracking
                continue
            raw_d = self.regular_upper[ch]
            nums = [float(n) for n in _NUMBER_RE.findall(raw_d)]
            xs = nums[0::2]
            min_x, max_x = min(xs), max(xs)
            items.append((cursor - min_x, raw_d))
            advance = max_x - min_x
            if idx < len(clean) - 1 and clean[idx + 1] != " ":
                advance += tracking
            elif idx < len(clean) - 1 and clean[idx + 1] == " ":
                advance += tracking
            cursor += advance
        start_x = center_x - cursor / 2.0
        parts: list[str] = []
        for gx, d in items:
            if d:
                parts.append(
                    f'<g fill="{fill}" fill-opacity="1"><g transform="translate({start_x + gx:.6f}, {baseline_y:.6f})">'
                    f'<g><path d="{d}"/></g></g></g>'
                )
            else:
                parts.append(
                    f'<g fill="{fill}" fill-opacity="1"><g transform="translate({start_x + gx:.6f}, {baseline_y:.6f})">'
                    f"<g/></g></g>"
                )
        return "".join(parts)


@dataclass(frozen=True, slots=True)
class ProjectBrandSpec:
    """Metadata and geometry configuration for a single ecosystem project's brand pack."""

    slug: str
    title: str
    header_text: str
    sub_text: str
    subtitle: str
    icon_key: str
    legacy_label: str | None = None
    standalone_inline: bool = False

    @staticmethod
    def stroke_attrs(color: str = GOLD, width: int = 14) -> str:
        """Return standard monoline SVG stroke attributes for the given color."""
        return f'fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"'

    def svg_body(self, color: str = GOLD, font: VectorFont | None = None) -> str:
        """Return the inner 256x256 SVG path and shape elements in the requested stroke/fill color."""
        sa = self.stroke_attrs(color, 14)
        sa12 = self.stroke_attrs(color, 12)

        if self.icon_key == "litestar" and font is not None:
            path_lines = "\n".join(
                f'    <path fill="{color}" d="{d}" fill-opacity="1" fill-rule="nonzero"/>'
                for d in font.litestar_badge_paths
            )
            return f'  <g transform="translate(-2.4, -2.4) scale(0.70)">\n{path_lines}\n  </g>'

        bodies: dict[str, str] = {
            "litestar": f"""  <path d="M204 92A86 86 0 1 1 92 48" {sa}/>
  <path d="M148 52L163 92L206 92L171 117L185 158L148 133L111 158L125 117L90 92L133 92Z" {sa}/>""",
            "sqlspec": f"""  <ellipse cx="104" cy="56" rx="72" ry="26" {sa}/>
  <path d="M32 56V180" {sa}/>
  <path d="M176 56V100" {sa}/>
  <path d="M32 118C32 132.36 64.24 144 104 144C108.5 144 112.9 143.85 117.1 143.56" {sa}/>
  <path d="M32 180C32 194.36 64.24 206 104 206C108.5 206 112.9 205.85 117.1 205.56" {sa}/>
  <rect x="136" y="124" width="92" height="92" rx="22" {sa}/>
  <path d="M160 154L180 170L160 186" {sa}/>
  <path d="M188 186H204" {sa}/>""",
            "advanced_alchemy": f"""  <rect x="92" y="24" width="72" height="24" rx="12" {sa}/>
  <path d="M106 48V86.5C68.5 96.8 42 131.2 42 172C42 213.97 80.5 236 128 236C175.5 236 214 213.97 214 172C214 131.2 187.5 96.8 150 86.5V48" {sa}/>
  <path d="M49 140C78 158 104 158 128 142C152 126 178 126 207 144" {sa}/>
  <circle cx="90" cy="186" r="14" {sa12}/>
  <circle cx="134" cy="206" r="11" {sa12}/>
  <circle cx="164" cy="174" r="9" {sa12}/>""",
            "pytest_databases": f"""  <ellipse cx="104" cy="56" rx="72" ry="26" {sa}/>
  <path d="M32 56V180" {sa}/>
  <path d="M176 56V104" {sa}/>
  <path d="M32 118C32 132.36 64.24 144 104 144C111.5 144 118.7 143.58 125.4 142.8" {sa}/>
  <path d="M32 180C32 194.36 64.24 206 104 206C108.5 206 112.9 205.85 117.1 205.56" {sa}/>
  <circle cx="182" cy="172" r="46" {sa}/>
  <path d="M161 172L175 186L205 156" {sa}/>""",
            "polyfactory": f"""  <path d="M128 28L216 78V178L128 228L40 178V78L128 28Z" {sa}/>
  <path d="M40 78L128 128L216 78" {sa}/>
  <path d="M128 128V228" {sa}/>
  <path d="M84 53L172 103" {sa12}/>
  <circle cx="84" cy="152" r="12" {sa12}/>
  <circle cx="172" cy="152" r="12" {sa12}/>""",
            "litestar_ai": f"""  <path d="M128 40C128 88.6 167.4 128 216 128C167.4 128 128 167.4 128 216C128 167.4 88.6 128 40 128C88.6 128 128 88.6 128 40Z" {sa}/>
  <circle cx="192" cy="64" r="14" {sa12}/>
  <circle cx="64" cy="192" r="14" {sa12}/>
  <circle cx="64" cy="64" r="8" fill="{color}"/>
  <circle cx="192" cy="192" r="8" fill="{color}"/>""",
            "litestar_skills": f"""  <rect x="28" y="40" width="200" height="176" rx="24" {sa}/>
  <path d="M28 88H228" {sa}/>
  <path d="M64 128L92 152L64 176" {sa}/>
  <path d="M104 176H132" {sa}/>
  <path d="M172 116L180 142L206 150L180 158L172 184L164 158L138 150L164 142Z" {sa12}/>""",
            "litestar_asyncpg": f"""  <ellipse cx="104" cy="56" rx="72" ry="26" {sa}/>
  <path d="M32 56V180" {sa}/>
  <path d="M176 56V104" {sa}/>
  <path d="M32 118C32 132.36 64.24 144 104 144C111.5 144 118.7 143.58 125.4 142.8" {sa}/>
  <path d="M32 180C32 194.36 64.24 206 104 206C108.5 206 112.9 205.85 117.1 205.56" {sa}/>
  <circle cx="182" cy="172" r="46" {sa}/>
  <path d="M188 148L170 172H186L176 196" {sa12}/>""",
            "litestar_oracledb": f"""  <ellipse cx="104" cy="56" rx="72" ry="26" {sa}/>
  <path d="M32 56V180" {sa}/>
  <path d="M176 56V114" {sa}/>
  <path d="M32 118C32 132.36 64.24 144 104 144C108.5 144 112.9 143.85 117.1 143.56" {sa}/>
  <path d="M32 180C32 194.36 64.24 206 104 206C108.5 206 112.9 205.85 117.1 205.56" {sa}/>
  <rect x="132" y="136" width="96" height="68" rx="34" {sa}/>""",
            "dtos": f"""  <path d="M80 40C58 40 48 52 48 74V104C48 118 36 128 24 128C36 128 48 138 48 152V182C48 204 58 216 80 216" {sa}/>
  <path d="M176 40C198 40 208 52 208 74V104C208 118 220 128 232 128C220 128 208 138 208 152V182C208 204 198 216 176 216" {sa}/>
  <path d="M96 92H160" {sa}/>
  <path d="M96 128H144" {sa}/>
  <path d="M96 164H160" {sa}/>""",
            "type_lens": f"""  <circle cx="112" cy="112" r="74" {sa}/>
  <path d="M164 164L224 224" {sa}/>
  <path d="M84 90L62 112L84 134" {sa12}/>
  <path d="M140 90L162 112L140 134" {sa12}/>
  <path d="M100 94H124" {sa12}/>
  <path d="M112 94V134" {sa12}/>""",
            "debug_toolbar": f"""  <rect x="28" y="40" width="200" height="176" rx="22" {sa}/>
  <path d="M28 88H228" {sa}/>
  <circle cx="60" cy="64" r="6" fill="{color}"/>
  <circle cx="84" cy="64" r="6" fill="{color}"/>
  <circle cx="108" cy="64" r="6" fill="{color}"/>
  <path d="M56 154H88L108 114L134 186L156 138L172 154H200" {sa}/>""",
            "litestar_email": f"""  <rect x="56" y="64" width="172" height="128" rx="20" {sa}/>
  <path d="M64 74L142 136L220 74" {sa}/>
  <path d="M20 96H36" {sa}/>
  <path d="M16 128H36" {sa}/>
  <path d="M24 160H36" {sa}/>""",
            "litestar_htmx": f"""  <path d="M72 68L24 128L72 188" {sa}/>
  <path d="M184 68L232 128L184 188" {sa}/>
  <path d="M96 104H160L140 84" {sa}/>
  <path d="M160 152H96L116 172" {sa}/>""",
            "litestar_vite": f"""  <path d="M148 24L52 140H126L102 232L204 112H130L148 24Z" {sa}/>""",
            "litestar_queues": f"""  <rect x="32" y="44" width="136" height="36" rx="18" {sa}/>
  <rect x="60" y="110" width="136" height="36" rx="18" {sa}/>
  <rect x="32" y="176" width="116" height="36" rx="18" {sa}/>
  <path d="M176 194H224" {sa}/>
  <path d="M204 174L224 194L204 214" {sa}/>""",
            "litestar_saq": f"""  <path d="M204 104A80 80 0 1 0 194 176" {sa}/>
  <path d="M204 68V106H166" {sa}/>
  <path d="M138 72L92 132H132L116 184L164 124H124L138 72Z" {sa}/>""",
            "litestar_mcp": f"""  <path d="M148 44L52 140C38.75 153.25 38.75 174.75 52 188C65.25 201.25 86.75 201.25 100 188L176 112" {sa}/>
  <path d="M80 144L156 68C169.25 54.75 190.75 54.75 204 68C217.25 81.25 217.25 102.75 204 116L108 212" {sa}/>
  <circle cx="156" cy="36" r="12" {sa}/>
  <circle cx="100" cy="220" r="12" {sa}/>""",
            "litestar_granian": f"""  <path d="M196 154A74 74 0 1 1 148 56" {sa}/>
  <path d="M28 182C80 198 144 176 208 92" {sa}/>
  <path d="M172 92H208V128" {sa}/>
  <circle cx="114" cy="116" r="20" {sa}/>""",
            "litestar_security": f"""  <path d="M128 28L48 60V120C48 174 82 214 128 232C174 214 208 174 208 120V60L128 28Z" {sa}/>
  <circle cx="128" cy="112" r="20" {sa}/>
  <path d="M128 132V176" {sa}/>""",
            "litestar_autowire": f"""  <path d="M128 84L166 106V150L128 172L90 150V106L128 84Z" {sa}/>
  <circle cx="128" cy="128" r="10" fill="{color}"/>
  <circle cx="52" cy="60" r="16" {sa}/>
  <path d="M64 72L94 102" {sa}/>
  <circle cx="204" cy="60" r="16" {sa}/>
  <path d="M192 72L162 102" {sa}/>
  <circle cx="52" cy="196" r="16" {sa}/>
  <path d="M64 184L94 154" {sa}/>
  <circle cx="204" cy="196" r="16" {sa}/>
  <path d="M192 184L162 154" {sa}/>""",
            "flow": f"""  <circle cx="52" cy="64" r="22" {sa}/>
  <circle cx="52" cy="192" r="22" {sa}/>
  <circle cx="156" cy="128" r="22" {sa}/>
  <path d="M74 64C112 64 108 128 134 128" {sa}/>
  <path d="M74 192C112 192 108 128 134 128" {sa}/>
  <path d="M178 128H232" {sa}/>
  <path d="M210 106L232 128L210 150" {sa}/>""",
        }
        return bodies[self.icon_key]

    def wrap_svg(
        self, body: str, width: int = CANVAS_SIZE, height: int = CANVAS_SIZE, viewbox: str = "0 0 256 256"
    ) -> str:
        """Wrap SVG elements in a standard root element."""
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="{viewbox}" fill="none" role="img" aria-label="{self.title}">\n'
            f"  <title>{self.title}</title>\n"
            f"{body}\n"
            f"</svg>\n"
        )

    def inline_banner_svg(self, font: VectorFont, dark: bool = True) -> str:
        """Build a 1600x388 (viewBox 1200x291) 2-tier inline banner matching the original Litestar typography."""
        if self.icon_key == "litestar":
            icon_block = font.litestar_star_dark if dark else font.litestar_star_light
        else:
            icon_block = f'<g transform="translate(230.0, 36.5) scale(0.85)">\n{self.svg_body(GOLD, font)}\n</g>'

        header_color = WHITE if dark else NAVY
        sub_color = WHITE if dark else LEGACY_SUB_LIGHT
        sub_y = 214.882456 if dark else 212.215453
        line_stroke = GOLD if dark else "#000000"

        if self.header_text == "LITESTAR":
            header_block = font.litestar_header_dark if dark else font.litestar_header_light
            center_x = 793.6
        else:
            center_x, header_block = font.render_bold_header(
                self.header_text, start_x=543.6, baseline_y=155.83, fill=header_color
            )

        sub_block = font.render_regular_centered(self.sub_text, center_x=center_x, baseline_y=sub_y, fill=sub_color)
        divider = (
            f'<path stroke-linecap="round" transform="matrix(0, 0.75, -0.75, 0, 511.169216, 40.05441)" '
            f'fill="none" stroke-linejoin="miter" d="M 1.50037 1.501663 L 279.65144 1.501663 " '
            f'stroke="{line_stroke}" stroke-width="3" stroke-opacity="1" stroke-miterlimit="4"/>'
        )
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            'width="1600" zoomAndPan="magnify" viewBox="0 0 1200 290.999983" height="388" '
            'preserveAspectRatio="xMidYMid meet" version="1.0">'
            f"{icon_block}{header_block}{sub_block}{divider}</svg>"
        )

    def legacy_litestar_inline_svg(self, font: VectorFont, label_text: str, dark: bool = True) -> str:
        """Build a legacy LITESTAR / <LABEL> transparent inline banner matching existing Branding - SVG - Transparent files."""
        star_block = font.litestar_star_dark if dark else font.litestar_star_light
        header_block = font.litestar_header_dark if dark else font.litestar_header_light
        sub_color = WHITE if dark else LEGACY_SUB_LIGHT
        sub_y = 214.882456 if dark else 212.215453
        line_stroke = GOLD if dark else "#000000"
        sub_block = font.render_regular_centered(label_text, center_x=793.6, baseline_y=sub_y, fill=sub_color)
        divider = (
            f'<path stroke-linecap="round" transform="matrix(0, 0.75, -0.75, 0, 511.169216, 40.05441)" '
            f'fill="none" stroke-linejoin="miter" d="M 1.50037 1.501663 L 279.65144 1.501663 " '
            f'stroke="{line_stroke}" stroke-width="3" stroke-opacity="1" stroke-miterlimit="4"/>'
        )
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            'width="1600" zoomAndPan="magnify" viewBox="0 0 1200 290.999983" height="388" '
            'preserveAspectRatio="xMidYMid meet" version="1.0">'
            f"{star_block}{header_block}{sub_block}{divider}</svg>"
        )


PROJECTS: tuple[ProjectBrandSpec, ...] = (
    ProjectBrandSpec(
        "litestar",
        "Litestar",
        "LITESTAR",
        "FRAMEWORK",
        "Light, Flexible & Extensible ASGI Framework",
        "litestar",
        legacy_label=None,
        standalone_inline=True,
    ),
    ProjectBrandSpec(
        "sqlspec",
        "SQLSpec",
        "SQLSPEC",
        "DATABASE",
        "SQL Query Specification & Driver Execution Engine",
        "sqlspec",
        legacy_label="SQLSpec",
        standalone_inline=True,
    ),
    ProjectBrandSpec(
        "advanced-alchemy",
        "Advanced Alchemy",
        "ADVANCED",
        "ALCHEMY",
        "SQLAlchemy Repository, Service & Migration Toolkit",
        "advanced_alchemy",
        legacy_label="Advanced Alchemy",
        standalone_inline=True,
    ),
    ProjectBrandSpec(
        "pytest-databases",
        "Pytest Databases",
        "PYTEST",
        "DATABASES",
        "Containerized Database Fixtures for Pytest",
        "pytest_databases",
        legacy_label="Pytest Databases",
        standalone_inline=True,
    ),
    ProjectBrandSpec(
        "polyfactory",
        "Polyfactory",
        "LITESTAR",
        "POLYFACTORY",
        "Simple & Powerful Mock Data Generation Factories",
        "polyfactory",
        legacy_label=None,
        standalone_inline=False,
    ),
    ProjectBrandSpec(
        "dtos",
        "DTOs",
        "LITESTAR",
        "DTOS",
        "High-Performance Data Transfer Objects & Domain Modeling",
        "dtos",
        legacy_label=None,
        standalone_inline=False,
    ),
    ProjectBrandSpec(
        "type-lens",
        "Type Lens",
        "LITESTAR",
        "TYPE LENS",
        "Runtime Type Introspection & Annotation Utilities",
        "type_lens",
        legacy_label=None,
        standalone_inline=False,
    ),
    ProjectBrandSpec(
        "debug-toolbar",
        "Debug Toolbar",
        "LITESTAR",
        "DEBUG TOOLBAR",
        "Interactive Request, SQL & Profiling Toolbar for Litestar",
        "debug_toolbar",
        legacy_label="Debug Toolbar",
        standalone_inline=False,
    ),
    ProjectBrandSpec(
        "litestar-ai",
        "Litestar AI",
        "LITESTAR",
        "AI",
        "Google ADK, GenAI & Agentic Runtime Integration",
        "litestar_ai",
        legacy_label="AI",
        standalone_inline=False,
    ),
    ProjectBrandSpec(
        "litestar-skills",
        "Litestar Skills",
        "LITESTAR",
        "SKILLS",
        "First-Party Agent Skills, Subagents & MCP Tooling",
        "litestar_skills",
        legacy_label="Skills",
        standalone_inline=False,
    ),
    ProjectBrandSpec(
        "litestar-asyncpg",
        "Litestar AsyncPG",
        "LITESTAR",
        "ASYNCPG",
        "High-Performance PostgreSQL Connection Plugin",
        "litestar_asyncpg",
        legacy_label=None,
        standalone_inline=False,
    ),
    ProjectBrandSpec(
        "litestar-oracledb",
        "Litestar OracleDB",
        "LITESTAR",
        "ORACLEDB",
        "Async & Sync Oracle Database Plugin",
        "litestar_oracledb",
        legacy_label=None,
        standalone_inline=False,
    ),
    ProjectBrandSpec(
        "litestar-vite",
        "Litestar Vite",
        "LITESTAR",
        "VITE",
        "Vite, Inertia.js & Modern Frontend Integration",
        "litestar_vite",
        legacy_label=None,
        standalone_inline=False,
    ),
    ProjectBrandSpec(
        "litestar-granian",
        "Litestar Granian",
        "LITESTAR",
        "GRANIAN",
        "High-Performance Rust HTTP/ASGI Server Plugin",
        "litestar_granian",
        legacy_label=None,
        standalone_inline=False,
    ),
    ProjectBrandSpec(
        "litestar-mcp",
        "Litestar MCP",
        "LITESTAR",
        "MCP",
        "Model Context Protocol & A2A Integration",
        "litestar_mcp",
        legacy_label="MCP",
        standalone_inline=False,
    ),
    ProjectBrandSpec(
        "litestar-queues",
        "Litestar Queues",
        "LITESTAR",
        "QUEUES",
        "Multi-Backend Async Task & Message Queues",
        "litestar_queues",
        legacy_label="Queues",
        standalone_inline=False,
    ),
    ProjectBrandSpec(
        "litestar-saq",
        "Litestar SAQ",
        "LITESTAR",
        "SAQ",
        "Simple Async Queues Worker & Cron Plugin",
        "litestar_saq",
        legacy_label=None,
        standalone_inline=False,
    ),
    ProjectBrandSpec(
        "litestar-security",
        "Litestar Security",
        "LITESTAR",
        "SECURITY",
        "Authentication, Authorization & Guard Primitives",
        "litestar_security",
        legacy_label="Security",
        standalone_inline=False,
    ),
    ProjectBrandSpec(
        "litestar-autowire",
        "Litestar Autowire",
        "LITESTAR",
        "AUTOWIRE",
        "Automatic Domain & Dependency Wiring",
        "litestar_autowire",
        legacy_label="Autowire",
        standalone_inline=False,
    ),
    ProjectBrandSpec(
        "litestar-email",
        "Litestar Email",
        "LITESTAR",
        "EMAIL",
        "Multi-Provider Transactional Email Plugin",
        "litestar_email",
        legacy_label="Email",
        standalone_inline=False,
    ),
    ProjectBrandSpec(
        "litestar-htmx",
        "Litestar HTMX",
        "LITESTAR",
        "HTMX",
        "Server-Driven Hypermedia & HX-Swap Utilities",
        "litestar_htmx",
        legacy_label="HTMX",
        standalone_inline=False,
    ),
    ProjectBrandSpec(
        "flow",
        "Flow",
        "LITESTAR",
        "FLOW",
        "Spec-First Engineering & Directed Agent Workflows",
        "flow",
        legacy_label="Flow",
        standalone_inline=True,
    ),
)


def rasterize_svg_to_png(svg_path: Path, png_path: Path, width: int, height: int) -> None:
    """Rasterize an SVG file to a straight-alpha RGBA PNG at the given dimensions using ffmpeg/librsvg."""
    subprocess.run(
        [
            FFMPEG_BIN,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-width",
            str(width),
            "-height",
            str(height),
            "-i",
            str(svg_path),
            "-vf",
            "format=rgba,unpremultiply=inplace=1",
            "-frames:v",
            "1",
            str(png_path),
        ],
        check=True,
    )


def write_multi_res_ico(png_paths: list[tuple[int, Path]], ico_path: Path) -> None:
    """Pack multiple square PNG images into a standard Windows ICO container."""
    payloads = [(sz, p.read_bytes()) for sz, p in png_paths]
    header = struct.pack("<HHH", 0, 1, len(payloads))
    offset = 6 + 16 * len(payloads)
    entries: list[bytes] = []
    for sz, data in payloads:
        dim = 0 if sz >= 256 else sz
        entries.append(struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(data), offset))
        offset += len(data)
    ico_path.write_bytes(header + b"".join(entries) + b"".join(data for _, data in payloads))


def padded_square_svg(spec: ProjectBrandSpec, font: VectorFont, pad_canvas: int = 300) -> str:
    """Wrap the gold project icon centered on a solid navy square with safe-zone margin."""
    offset = (pad_canvas - CANVAS_SIZE) / 2.0
    body = (
        f'  <rect x="0" y="0" width="{pad_canvas}" height="{pad_canvas}" fill="{NAVY}"/>\n'
        f'  <g transform="translate({offset:.1f}, {offset:.1f})">\n'
        f"{spec.svg_body(GOLD, font)}\n"
        f"  </g>"
    )
    return spec.wrap_svg(body, width=pad_canvas, height=pad_canvas, viewbox=f"0 0 {pad_canvas} {pad_canvas}")


def generate_project_pack(spec: ProjectBrandSpec, root_dir: Path, font: VectorFont) -> None:
    """Generate svg/, png/, banners/, and favicons/ for a single project."""
    proj_dir = root_dir / spec.slug
    svg_dir = proj_dir / "svg"
    png_dir = proj_dir / "png"
    banners_dir = proj_dir / "banners"
    favicons_dir = proj_dir / "favicons"

    for d in (svg_dir, png_dir, banners_dir, favicons_dir):
        d.mkdir(parents=True, exist_ok=True)

    for obsolete in (
        svg_dir / "banner-dark.svg",
        svg_dir / "banner-light.svg",
        banners_dir / "banner-dark.png",
        banners_dir / "banner-light.png",
        banners_dir / "og-social-dark.png",
        banners_dir / "og-social-light.png",
    ):
        obsolete.unlink(missing_ok=True)

    icon_gold_svg = spec.wrap_svg(spec.svg_body(GOLD, font))
    icon_navy_svg = spec.wrap_svg(spec.svg_body(NAVY, font))
    icon_white_svg = spec.wrap_svg(spec.svg_body(WHITE, font))

    badge_dark_svg = spec.wrap_svg(
        f'  <rect x="8" y="8" width="240" height="240" rx="52" fill="{NAVY}" stroke="{GOLD}" stroke-width="6"/>\n'
        + spec.svg_body(GOLD, font)
    )
    badge_light_svg = spec.wrap_svg(
        f'  <rect x="8" y="8" width="240" height="240" rx="52" fill="{LIGHT_BG}" stroke="{SLATE_BORDER}" stroke-width="6"/>\n'
        + spec.svg_body(GOLD, font)
    )
    square_dark_svg = spec.wrap_svg(
        f'  <rect x="0" y="0" width="256" height="256" fill="{NAVY}"/>\n' + spec.svg_body(GOLD, font)
    )

    (svg_dir / "icon-gold.svg").write_text(icon_gold_svg, encoding="utf-8")
    (svg_dir / "icon-navy.svg").write_text(icon_navy_svg, encoding="utf-8")
    (svg_dir / "icon-white.svg").write_text(icon_white_svg, encoding="utf-8")
    (svg_dir / "badge-dark.svg").write_text(badge_dark_svg, encoding="utf-8")
    (svg_dir / "badge-light.svg").write_text(badge_light_svg, encoding="utf-8")
    (svg_dir / "square-dark.svg").write_text(square_dark_svg, encoding="utf-8")

    banner_inline_dark_svg = spec.inline_banner_svg(font, dark=True)
    banner_inline_light_svg = spec.inline_banner_svg(font, dark=False)
    (svg_dir / "banner-inline-dark.svg").write_text(banner_inline_dark_svg, encoding="utf-8")
    (svg_dir / "banner-inline-light.svg").write_text(banner_inline_light_svg, encoding="utf-8")
    rasterize_svg_to_png(svg_dir / "banner-inline-dark.svg", banners_dir / "banner-inline-dark.png", 1600, 388)
    rasterize_svg_to_png(svg_dir / "banner-inline-light.svg", banners_dir / "banner-inline-light.png", 1600, 388)

    for sz in (64, 128, 256, 512, 1024):
        rasterize_svg_to_png(svg_dir / "icon-gold.svg", png_dir / f"icon-gold-{sz}.png", sz, sz)
    shutil.copyfile(png_dir / "icon-gold-256.png", png_dir / "logo-default.png")

    rasterize_svg_to_png(svg_dir / "icon-navy.svg", png_dir / "icon-navy-512.png", 512, 512)
    rasterize_svg_to_png(svg_dir / "icon-white.svg", png_dir / "icon-white-512.png", 512, 512)
    rasterize_svg_to_png(svg_dir / "badge-dark.svg", png_dir / "badge-dark-512.png", 512, 512)
    rasterize_svg_to_png(svg_dir / "badge-light.svg", png_dir / "badge-light-512.png", 512, 512)

    pad300_svg = favicons_dir / "_tmp_pad300.svg"
    pad310_svg = favicons_dir / "_tmp_pad310.svg"
    pad300_svg.write_text(padded_square_svg(spec, font, 300), encoding="utf-8")
    pad310_svg.write_text(padded_square_svg(spec, font, 310), encoding="utf-8")

    rasterize_svg_to_png(pad300_svg, png_dir / "square-dark-512.png", 512, 512)

    (favicons_dir / "favicon.svg").write_text(icon_gold_svg, encoding="utf-8")
    for fsz in (16, 32, 48):
        rasterize_svg_to_png(svg_dir / "icon-gold.svg", favicons_dir / f"favicon-{fsz}x{fsz}.png", fsz, fsz)
    shutil.copyfile(png_dir / "icon-gold-64.png", favicons_dir / "favicon.png")

    write_multi_res_ico(
        [
            (16, favicons_dir / "favicon-16x16.png"),
            (32, favicons_dir / "favicon-32x32.png"),
            (48, favicons_dir / "favicon-48x48.png"),
        ],
        favicons_dir / "favicon.ico",
    )

    rasterize_svg_to_png(pad310_svg, favicons_dir / "apple-touch-icon.png", 180, 180)
    rasterize_svg_to_png(pad300_svg, favicons_dir / "android-chrome-192x192.png", 192, 192)
    rasterize_svg_to_png(pad300_svg, favicons_dir / "android-chrome-512x512.png", 512, 512)
    pad300_svg.unlink(missing_ok=True)
    pad310_svg.unlink(missing_ok=True)

    manifest_payload = {
        "name": spec.title,
        "short_name": spec.slug,
        "icons": [
            {"src": "/android-chrome-192x192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/android-chrome-512x512.png", "sizes": "512x512", "type": "image/png"},
        ],
        "theme_color": NAVY,
        "background_color": NAVY,
        "display": "standalone",
    }
    (favicons_dir / "site.webmanifest").write_text(json.dumps(manifest_payload, indent=2) + "\n", encoding="utf-8")

    head_tags = (
        f'<link rel="icon" type="image/svg+xml" href="/favicon.svg">\n'
        f'<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">\n'
        f'<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">\n'
        f'<link rel="shortcut icon" href="/favicon.ico">\n'
        f'<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">\n'
        f'<link rel="manifest" href="/site.webmanifest">\n'
        f'<meta name="theme-color" content="{NAVY}">\n'
    )
    (favicons_dir / "head-tags.html").write_text(head_tags, encoding="utf-8")


def generate_legacy_inline_banners(font: VectorFont) -> None:
    """Generate missing inline SVG/PNG banners in Branding - SVG/PNG - Transparent without overwriting originals."""
    LEGACY_SVG_TRANSPARENT_DIR.mkdir(parents=True, exist_ok=True)
    LEGACY_PNG_TRANSPARENT_DIR.mkdir(parents=True, exist_ok=True)

    for spec in PROJECTS:
        if not spec.legacy_label:
            continue
        for is_dark, mode_label in ((True, "Dark"), (False, "Light")):
            svg_name = f"{spec.legacy_label} - Banner - Inline - {mode_label}.svg"
            svg_target = LEGACY_SVG_TRANSPARENT_DIR / svg_name
            if spec.standalone_inline:
                svg_content = spec.inline_banner_svg(font, dark=is_dark)
            else:
                svg_content = spec.legacy_litestar_inline_svg(font, spec.legacy_label, dark=is_dark)
            svg_target.write_text(svg_content, encoding="utf-8")
            png_target = LEGACY_PNG_TRANSPARENT_DIR / f"{svg_target.stem}.png"
            rasterize_svg_to_png(svg_target, png_target, 5000, 1213)

    for svg_file in sorted(LEGACY_SVG_TRANSPARENT_DIR.glob("* - Banner - Inline - *.svg")):
        png_target = LEGACY_PNG_TRANSPARENT_DIR / f"{svg_file.stem}.png"
        if not png_target.exists():
            rasterize_svg_to_png(svg_file, png_target, 5000, 1213)


def write_projects_readme_and_gallery(root_dir: Path) -> None:
    """Write the Branding Pack documentation and interactive HTML gallery in assets/projects/."""
    rows = "\n".join(
        f"| `{p.slug}` | **{p.title}** | {p.subtitle} | [`{p.slug}/svg/icon-gold.svg`]({p.slug}/svg/icon-gold.svg) | [`{p.slug}/svg/banner-inline-dark.svg`]({p.slug}/svg/banner-inline-dark.svg) |"
        for p in PROJECTS
    )
    readme = f"""# Litestar Ecosystem Branding Pack

Unified vector and raster branding pack across all {len(PROJECTS)} ecosystem packages.

## Brand Specifications

- **Primary Accent (Litestar Gold)**: `#EDB641` (`rgb(237, 182, 65)`)
- **Primary Dark Surface (Litestar Navy)**: `#202235` (`rgb(32, 34, 53)`)
- **Primary Light Surface**: `#F8FAFC` / `#FFFFFF`
- **Vector Grid**: `256x256` (`viewBox="0 0 256 256"`), `stroke-width="14"`, `stroke-linecap="round"`, `stroke-linejoin="round"`

## Included Projects ({len(PROJECTS)})

| Slug | Project | Description | Master Vector | Inline Banner |
| :--- | :--- | :--- | :--- | :--- |
{rows}

## Per-Project Folder Layout

Each `<project-slug>/` directory contains:

- **`svg/`**:
  - `icon-gold.svg` — Primary `#EDB641` monoline vector icon on transparent background (`logo.svg` / `logo-icon.svg`)
  - `icon-navy.svg` — Monochrome `#202235` vector icon on transparent background
  - `icon-white.svg` — Monochrome `#FFFFFF` vector icon on transparent background
  - `badge-dark.svg` — `#EDB641` icon on rounded `#202235` app tile with gold border
  - `badge-light.svg` — `#EDB641` icon on rounded `#F8FAFC` app tile
  - `square-dark.svg` — `#EDB641` icon on solid `#202235` square avatar tile
  - `banner-inline-dark.svg` & `banner-inline-light.svg` — `1600x388` transparent 2-tier horizontal lockup banners (icon + vertical divider + Inter Bold header + Inter Thin subheader)
- **`png/`**:
  - `icon-gold-{{64,128,256,512,1024}}.png` & `logo-default.png` (`256x256` transparent)
  - `icon-navy-512.png` & `icon-white-512.png`
  - `badge-dark-512.png`, `badge-light-512.png`, `square-dark-512.png`
- **`banners/`**:
  - `banner-inline-dark.png` & `banner-inline-light.png` (`1600x388` transparent README hero banners)
- **`favicons/`**:
  - `favicon.svg` (scalable vector favicon)
  - `favicon.ico` (multi-resolution `16x16`, `32x32`, `48x48` ICO container)
  - `favicon-16x16.png`, `favicon-32x32.png`, `favicon-48x48.png`, `favicon.png` (`64x64`)
  - `apple-touch-icon.png` (`180x180` on solid `#202235` with safe-zone margin)
  - `android-chrome-192x192.png` & `android-chrome-512x512.png`
  - `site.webmanifest` and `head-tags.html`

## Regenerating the Pack

```bash
uv run python tools/generate_branding_pack.py
```
"""
    (root_dir / "README.md").write_text(readme, encoding="utf-8")

    js_entries = ",\n        ".join(f'["{p.slug}", "{p.title}"]' for p in PROJECTS)
    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Litestar Ecosystem Branding Pack</title>
  <link rel="icon" type="image/svg+xml" href="litestar/favicons/favicon.svg">
  <style>
    :root {{
      --navy: #202235;
      --surface: #2a2d40;
      --gold: #EDB641;
      --light: #F8FAFC;
      --text: #F1F5F9;
      --muted: #94A3B8;
      --border: #334155;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      padding: 2.5rem 2rem;
      background: var(--navy);
      color: var(--text);
      font-family: Inter, system-ui, -apple-system, sans-serif;
      line-height: 1.5;
    }}
    header {{
      max-width: 1400px;
      margin: 0 auto 2.5rem;
      border-bottom: 1px solid var(--border);
      padding-bottom: 1.5rem;
    }}
    h1 {{
      margin: 0 0 0.5rem;
      font-size: 2rem;
      letter-spacing: 0.04em;
      color: var(--gold);
    }}
    header p {{
      margin: 0;
      color: var(--muted);
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(620px, 1fr));
      gap: 1.75rem;
      max-width: 1400px;
      margin: 0 auto;
    }}
    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 1.5rem;
    }}
    .card h2 {{
      margin: 0 0 0.25rem;
      font-size: 1.25rem;
      color: var(--text);
    }}
    .card .slug {{
      font-family: monospace;
      color: var(--gold);
      font-size: 0.9rem;
      margin-bottom: 1rem;
      display: block;
    }}
    .swatches {{
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 0.75rem;
      margin-bottom: 1rem;
    }}
    .swatch {{
      border-radius: 8px;
      padding: 0.75rem;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      border: 1px solid var(--border);
    }}
    .swatch.dark {{ background: var(--navy); }}
    .swatch.light {{ background: var(--light); color: var(--navy); }}
    .swatch img {{ width: 64px; height: 64px; object-fit: contain; }}
    .swatch span {{ font-size: 0.72rem; opacity: 0.85; text-align: center; }}
    .banners {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.75rem;
    }}
    .banners .banner-box {{
      border-radius: 6px;
      border: 1px solid var(--border);
      padding: 0.4rem;
    }}
    .banners .banner-box.dark {{ background: var(--navy); }}
    .banners .banner-box.light {{ background: var(--light); }}
    .banners img {{
      width: 100%;
      display: block;
    }}
  </style>
</head>
<body>
  <header>
    <h1>Litestar Ecosystem Branding Pack</h1>
    <p>{len(PROJECTS)} projects &bull; Litestar Gold (<code>#EDB641</code>) &amp; Litestar Navy (<code>#202235</code>) &bull; SVGs, Multi-Res PNGs, Favicons &amp; 2-Tier Inline Lockups</p>
  </header>
  <main class="grid">
    <script>
      const projects = [
        {js_entries}
      ];
      const grid = document.querySelector(".grid");
      for (const [slug, title] of projects) {{
        const card = document.createElement("section");
        card.className = "card";
        card.innerHTML = `
          <h2>${{title}}</h2>
          <span class="slug">${{slug}}/</span>
          <div class="swatches">
            <div class="swatch dark"><img src="${{slug}}/svg/icon-gold.svg" alt="${{title}} Gold"><span>Gold SVG (Dark)</span></div>
            <div class="swatch light"><img src="${{slug}}/svg/icon-gold.svg" alt="${{title}} Gold Light"><span>Gold SVG (Light)</span></div>
            <div class="swatch light"><img src="${{slug}}/svg/icon-navy.svg" alt="${{title}} Navy"><span>Navy SVG</span></div>
            <div class="swatch dark"><img src="${{slug}}/svg/badge-dark.svg" alt="${{title}} App Badge"><span>App Badge</span></div>
            <div class="swatch dark"><img src="${{slug}}/favicons/apple-touch-icon.png" alt="${{title}} Touch Icon"><span>Touch / Fav</span></div>
          </div>
          <div class="banners">
            <div class="banner-box dark"><img src="${{slug}}/svg/banner-inline-dark.svg" alt="${{title}} Inline Dark Banner"></div>
            <div class="banner-box light"><img src="${{slug}}/svg/banner-inline-light.svg" alt="${{title}} Inline Light Banner"></div>
          </div>
        `;
        grid.appendChild(card);
      }}
    </script>
  </main>
</body>
</html>
"""
    (root_dir / "index.html").write_text(index_html, encoding="utf-8")


def main() -> None:
    """Build the complete Branding Pack for all 22 ecosystem projects and missing inline banners."""
    args = [a for a in sys.argv[1:] if a != "--force"]
    target_dir = Path(args[0]) if args else BRANDING_OUT_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    font = VectorFont.load_from_repo(REPO_ROOT)
    for spec in PROJECTS:
        generate_project_pack(spec, target_dir, font)
    generate_legacy_inline_banners(font)
    write_projects_readme_and_gallery(target_dir)
    sys.stdout.write(f"Generated branding pack for {len(PROJECTS)} projects in {target_dir}\n")


if __name__ == "__main__":
    main()
