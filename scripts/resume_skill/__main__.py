from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .init_data import init_workspace
from .jd_image import parse_jd_image
from .pipeline import build_resume


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="resume_skill", description="JD screenshot/text to tailored Chinese resume")
    sub = parser.add_subparsers(dest="command", required=True)

    init_parser = sub.add_parser("init", help="create local profile and experience files")
    init_parser.add_argument("--dir", default=".", help="workspace to initialize")

    build = sub.add_parser("build", help="build a tailored resume")
    build.add_argument("jd_file", nargs="?", help="JD text file (.txt or .md). Reads stdin if omitted and --image is not used.")
    build.add_argument("--image", help="JD screenshot path; requires VISION_API_KEY unless the Agent extracts text first")
    build.add_argument("--experiences", help="path to my_experiences.local.json")
    build.add_argument("--profile", help="path to my_profile.local.json")
    build.add_argument("--photo", help="path to photo file")
    build.add_argument("--template", default="classic_zh", help="template name or path")
    build.add_argument("--output-dir", help="output directory")
    build.add_argument("--title", help="override job title")
    build.add_argument("--company", help="company name")
    build.add_argument("--role", help="target role filter")
    build.add_argument("--name", help="override profile name")
    build.add_argument("--phone", help="override profile phone")
    build.add_argument("--email", help="override profile email")
    build.add_argument("--location", help="override profile location")
    build.add_argument("--min-score", type=float, default=0.0)
    build.add_argument("--max-tailored", type=int, default=7)
    build.add_argument("--one-page", dest="one_page", action="store_true", default=True, help="force one-page resume output; default")
    build.add_argument("--allow-multipage", dest="one_page", action="store_false", help="render fuller multi-page content")
    build.add_argument("--pdf", action="store_true", help="export resume.pdf with Chrome/Edge when available")

    args = parser.parse_args(argv)

    if args.command == "init":
        for message in init_workspace(Path(args.dir)):
            print(f"[resume-skill] {message}")
        return 0

    if args.command == "build":
        try:
            jd_text = read_jd_text(args)
            result = build_resume(
                jd_text,
                experiences_path=args.experiences,
                profile_path=args.profile,
                photo_path=args.photo,
                template=args.template,
                output_dir=args.output_dir,
                title=args.title,
                company=args.company,
                role=args.role,
                min_score=args.min_score,
                max_tailored=args.max_tailored,
                one_page=args.one_page,
                make_pdf=args.pdf,
                source_image=args.image,
                profile_overrides={
                    "name": args.name,
                    "phone": args.phone,
                    "email": args.email,
                    "location": args.location,
                },
            )
        except Exception as exc:
            print(f"[resume-skill] Error: {exc}", file=sys.stderr)
            return 1

        print("[resume-skill] Done")
        print(f"  output: {result['output_dir']}")
        print(f"  draft:  {result['draft_resume']}")
        print(f"  html:   {result['resume_html']}")
        if result["resume_pdf"]:
            suffix = f" ({result['pdf_pages']} page)" if result.get("pdf_pages") else ""
            print(f"  pdf:    {result['resume_pdf']}{suffix}")
        elif args.pdf:
            print(f"  pdf:    {result['pdf_message']}")
        print(f"  matched {result['selected_count']} / {result['experience_count']} experiences; rendered {result['rendered_count']} using {result['render_budget']} budget")
        return 0

    return 1


def read_jd_text(args: argparse.Namespace) -> str:
    if args.image:
        return parse_jd_image(args.image)
    if args.jd_file:
        path = Path(args.jd_file)
        if not path.exists():
            raise FileNotFoundError(f"JD file not found: {path}")
        return path.read_text(encoding="utf-8")
    text = sys.stdin.read()
    if not text.strip():
        raise ValueError("empty JD text")
    return text


if __name__ == "__main__":
    raise SystemExit(main())
