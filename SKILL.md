---
name: resume-skill
description: >
  Use when the user wants to generate, tailor, or export a Chinese resume from a
  job description, JD screenshot, JD image, or pasted JD text. This skill uses a
  local profile, photo, resume template, and verified experience database to
  produce draft_resume.md, resume.html, and optional resume.pdf.
---

# Resume Skill

Turn a JD screenshot into a targeted Chinese resume in three user-facing steps:
install the skill, put personal files in `data/`, then send a JD screenshot.

## Non-Negotiables

- Do not fabricate schools, companies, metrics, dates, certificates, or personal details.
- Do not include experiences where `needs_verification` is `true`.
- Keep private user data in `data/*.local.json`; do not ask the user to commit it.
- Put every generated artifact in one `resume_output_<timestamp>/` folder.
- If screenshot OCR is unavailable, ask the user to paste the JD text and continue.
- Generated PDFs must be one page by default. Trim lower-relevance content before shrinking text too far.

## Expected User Files

- `data/my_experiences.local.json`: required personal experience database.
- `data/my_profile.local.json`: optional name, contact, target title, and photo path.
- `data/photo.png` or another photo path passed with `--photo`: optional portrait.
- `templates/<name>/template.html` and `style.css`: optional custom template.

Run this once if the files do not exist:

```powershell
python -m pip install -e .
python -m resume_skill init
```

## JD Screenshot Workflow

1. Read the JD screenshot with available vision capability. If you can see the image, extract the JD text yourself and save it to a `.txt` file in the working folder.
2. Run the build command with the extracted text, local data, photo, and default template.
3. Report the generated paths and remind the user to review the draft before sending it.

Default command:

```powershell
python -m resume_skill build jd.txt --pdf
```

This command enforces one page by default. Use `--allow-multipage` only if the user explicitly asks for a fuller multi-page draft.

Image command when `VISION_API_KEY` is configured:

```powershell
python -m resume_skill build --image jd.jpg --pdf
```

Useful explicit command:

```powershell
python -m resume_skill build jd.txt --experiences data/my_experiences.local.json --profile data/my_profile.local.json --photo data/photo.png --template classic_zh --pdf
```

## Outputs

The build command creates:

- `jd_text.md`: JD text used for matching.
- `jd_analysis.json`: structured JD parse.
- `selected_experiences.json`: scored, filtered experience matches.
- `rendered_experiences.json`: the smaller subset actually rendered into the one-page resume.
- `draft_resume.md`: editable Markdown resume.
- `resume.html`: printable resume using the selected template.
- `resume.pdf`: optional, created only when `--pdf` and Chrome/Edge are available.

## Template Rules

Use `classic_zh` unless the user asks for another template. A custom template folder must contain:

- `template.html`
- `style.css`

Supported placeholders:

- `{{ style_css }}`
- `{{ name }}`
- `{{ title }}`
- `{{ contact_html }}`
- `{{ photo_html }}`
- `{{ sections_html }}`
- `{{ generated_at }}`
- `{{ density_class }}`

If the user uploads an HTML/CSS resume template, place it under `templates/<template_name>/`, convert its dynamic parts to the placeholders above, then run with `--template <template_name>`.
