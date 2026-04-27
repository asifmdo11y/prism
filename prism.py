#!/usr/bin/env python3
"""
prism - competitive intelligence from product screenshots

give it one or more screenshots of a competitor's product and get back:
- features visible in the UI
- UX patterns and design decisions
- information architecture notes
- gaps / opportunities relative to your own product
"""

import os
import sys
import base64
import argparse
import json
from pathlib import Path
from datetime import datetime

import anthropic


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

ANALYSIS_PROMPT = """You are a senior product manager doing a competitive analysis.

Analyze this product screenshot and extract structured intelligence. Be specific and concrete —
mention actual UI elements, copy, and interactions you can see. Don't speculate about things
not visible in the screenshot.

Return a JSON object with this structure:
{
  "product_name": "inferred product name or 'unknown'",
  "screen_type": "e.g. dashboard, onboarding, settings, checkout, etc.",
  "features_visible": [
    { "feature": "short name", "description": "what it does and how it's presented" }
  ],
  "ux_patterns": [
    { "pattern": "pattern name", "observation": "how it's used here" }
  ],
  "information_architecture": "brief note on navigation, layout, content hierarchy",
  "copy_tone": "how they talk to users — formal, casual, instructional, etc.",
  "design_observations": [
    "list of notable visual/design decisions"
  ],
  "what_stands_out": "1-2 sentences on the most interesting or differentiated thing in this screen"
}

Return only valid JSON, no markdown fences.
"""

COMPARISON_PROMPT = """You are a senior product manager synthesizing a competitive analysis from multiple product screenshots.

You've analyzed {n} screens. Here are the individual analyses:

{analyses}

Now synthesize across all of them:

Return a JSON object with this structure:
{
  "products_analyzed": ["list of product names"],
  "common_patterns": ["patterns seen across multiple products"],
  "differentiators": [
    { "product": "name", "differentiator": "what sets them apart" }
  ],
  "feature_matrix": {
    "feature_name": { "product_name": true/false }
  },
  "opportunity_gaps": [
    "things none of them do well, or missing features that users likely want"
  ],
  "overall_takeaways": [
    "3-5 concrete takeaways for a PM building in this space"
  ]
}

Return only valid JSON, no markdown fences.
"""


def load_image(path: Path) -> tuple[str, str]:
    """Returns (base64_data, media_type)."""
    ext = path.suffix.lower()
    media_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".gif": "image/gif",
    }
    media_type = media_map.get(ext, "image/png")
    data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
    return data, media_type


def analyze_single(client: anthropic.Anthropic, image_path: Path, extra_context: str = "") -> dict:
    """Analyze one screenshot."""
    print(f"  analyzing {image_path.name}...", flush=True)

    data, media_type = load_image(image_path)

    content = [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": data,
            },
        },
        {
            "type": "text",
            "text": ANALYSIS_PROMPT + (f"\n\nAdditional context: {extra_context}" if extra_context else ""),
        },
    ]

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1500,
        messages=[{"role": "user", "content": content}],
    )

    raw = message.content[0].text.strip()

    # sometimes models wrap in code fences anyway
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # return it as a raw observation if parsing fails
        return {"raw_analysis": raw, "parse_error": True}


def synthesize(client: anthropic.Anthropic, analyses: list[tuple[str, dict]]) -> dict:
    """Synthesize across multiple analyses."""
    print("\n  synthesizing across all screenshots...")

    formatted = "\n\n".join(
        f"=== {name} ===\n{json.dumps(analysis, indent=2)}"
        for name, analysis in analyses
    )

    prompt = COMPARISON_PROMPT.format(n=len(analyses), analyses=formatted)

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_synthesis": raw, "parse_error": True}


def format_single_report(name: str, analysis: dict) -> str:
    lines = [f"## {name}\n"]

    if analysis.get("parse_error"):
        return lines[0] + analysis.get("raw_analysis", "analysis failed") + "\n"

    lines.append(f"**Screen**: {analysis.get('screen_type', 'unknown')}")
    lines.append(f"**Product**: {analysis.get('product_name', 'unknown')}")
    lines.append("")

    features = analysis.get("features_visible", [])
    if features:
        lines.append("### Features Visible")
        for f in features:
            lines.append(f"- **{f.get('feature', '?')}** — {f.get('description', '')}")
        lines.append("")

    patterns = analysis.get("ux_patterns", [])
    if patterns:
        lines.append("### UX Patterns")
        for p in patterns:
            lines.append(f"- **{p.get('pattern', '?')}**: {p.get('observation', '')}")
        lines.append("")

    ia = analysis.get("information_architecture")
    if ia:
        lines.append(f"### IA / Layout\n{ia}\n")

    copy_tone = analysis.get("copy_tone")
    if copy_tone:
        lines.append(f"### Copy & Tone\n{copy_tone}\n")

    design = analysis.get("design_observations", [])
    if design:
        lines.append("### Design Observations")
        for d in design:
            lines.append(f"- {d}")
        lines.append("")

    standout = analysis.get("what_stands_out")
    if standout:
        lines.append(f"### What Stands Out\n{standout}\n")

    return "\n".join(lines)


def format_synthesis_report(synthesis: dict, image_names: list[str]) -> str:
    lines = ["## Synthesis\n"]

    if synthesis.get("parse_error"):
        return lines[0] + synthesis.get("raw_synthesis", "synthesis failed") + "\n"

    common = synthesis.get("common_patterns", [])
    if common:
        lines.append("### Patterns Across All Products")
        for p in common:
            lines.append(f"- {p}")
        lines.append("")

    diffs = synthesis.get("differentiators", [])
    if diffs:
        lines.append("### What Each Product Does Differently")
        for d in diffs:
            lines.append(f"- **{d.get('product', '?')}**: {d.get('differentiator', '')}")
        lines.append("")

    matrix = synthesis.get("feature_matrix", {})
    if matrix:
        products = sorted(set(p for v in matrix.values() for p in v.keys()))
        lines.append("### Feature Matrix")
        header = "| Feature | " + " | ".join(products) + " |"
        sep = "|---|" + "|".join("---" for _ in products) + "|"
        lines.append(header)
        lines.append(sep)
        for feature, presence in matrix.items():
            row = f"| {feature} | " + " | ".join(
                "✓" if presence.get(p) else "✗" for p in products
            ) + " |"
            lines.append(row)
        lines.append("")

    gaps = synthesis.get("opportunity_gaps", [])
    if gaps:
        lines.append("### Opportunity Gaps")
        for g in gaps:
            lines.append(f"- {g}")
        lines.append("")

    takeaways = synthesis.get("overall_takeaways", [])
    if takeaways:
        lines.append("### Key Takeaways")
        for i, t in enumerate(takeaways, 1):
            lines.append(f"{i}. {t}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="prism - competitive intelligence from product screenshots"
    )
    parser.add_argument(
        "images",
        nargs="+",
        help="screenshot files to analyze (.png, .jpg, .webp)"
    )
    parser.add_argument(
        "--context",
        "-c",
        help="extra context, e.g. 'this is a B2B SaaS project management tool'",
        default=""
    )
    parser.add_argument(
        "--output",
        "-o",
        help="save report to a markdown file",
        default=""
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="also save raw JSON analysis alongside the report"
    )
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("[prism] ANTHROPIC_API_KEY not set")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # validate images
    images = []
    for img_path in args.images:
        p = Path(img_path).resolve()
        if not p.exists():
            print(f"[prism] file not found: {p}")
            sys.exit(1)
        if p.suffix.lower() not in SUPPORTED_EXTENSIONS:
            print(f"[prism] unsupported format: {p.suffix} (supported: {', '.join(SUPPORTED_EXTENSIONS)})")
            sys.exit(1)
        images.append(p)

    print(f"[prism] analyzing {len(images)} screenshot(s)...")
    if args.context:
        print(f"[prism] context: {args.context}")
    print()

    individual_analyses = []
    for img in images:
        analysis = analyze_single(client, img, extra_context=args.context)
        individual_analyses.append((img.name, analysis))

    # build report
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    report_lines = [
        f"# Competitive Analysis",
        f"*generated by prism on {ts}*",
        "",
    ]

    if args.context:
        report_lines += [f"**Context**: {args.context}", ""]

    report_lines += ["---", ""]

    for name, analysis in individual_analyses:
        report_lines.append(format_single_report(name, analysis))
        report_lines.append("---\n")

    if len(individual_analyses) > 1:
        synthesis = synthesize(client, individual_analyses)
        report_lines.append(format_synthesis_report(synthesis, [n for n, _ in individual_analyses]))

    report = "\n".join(report_lines)

    print("\n" + report)

    if args.output:
        out = Path(args.output)
        out.write_text(report)
        print(f"\n[prism] report saved to {out}")

        if args.json:
            json_out = out.with_suffix(".json")
            json_out.write_text(json.dumps(
                {name: analysis for name, analysis in individual_analyses},
                indent=2
            ))
            print(f"[prism] JSON saved to {json_out}")


if __name__ == "__main__":
    main()
