# Experience Data

Use `data/my_experiences.local.json` for real private data.

Each item should describe one verified experience:

- `id`: stable unique id.
- `category`: `education`, `skill`, `project`, `internship`, `work`, or `certification`.
- `title`: resume-facing title.
- `subtitle`: role, company, school, or short context.
- `date_start`, `date_end`: `YYYY-MM`; use `null` for ongoing.
- `tags`: keywords used to match JD screenshots.
- `star_details`: verified text. Common keys are `situation`, `task`, `action`, `result`.
- `metrics`: optional verified numbers.
- `needs_verification`: set `true` for anything not safe to publish.

Never add fake metrics just to match a JD. If unsure, mark the entry as `needs_verification: true`.
