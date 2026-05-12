<p align="center">
  <a href="https://github.com/wangzichang224-design/One-Job-One-Resume">🔗</a>
</p>

<h1 align="center">一岗一简历</h1>

<hr>

<br>

<p align="center">
  <img src="./assets/offer-energy.png" alt="一岗一简历，马上拿 offer" width="520">
</p>

<h2 align="center">“一岗一简历，马上拿 offer”</h2>

<p align="center">
  <strong>把 JD 截图丢给 Agent，自动匹配你的本地资料库，生成一页定制中文简历。</strong>
</p>

<br>

<hr>

<p align="center">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-9b8c1a?style=for-the-badge">
  <img alt="Claude Code" src="https://img.shields.io/badge/Claude%20Code-Skill-4b4b4b?style=for-the-badge">
  <img alt="Codex" src="https://img.shields.io/badge/Codex-Skill-7c3aed?style=for-the-badge">
</p>

## 3 步开始

### 1. 安装 Skill

把这个链接发给 Codex / Claude Code / 其他 coding agent：

```text
https://github.com/wangzichang224-design/One-Job-One-Resume
```

然后对 Agent 说：

```text
请把这个仓库安装成 skill。
如果需要本地目录名，请命名为 resume-skill。
安装后请运行：
python -m pip install -e .
python -m resume_skill init
```

仓库名不需要带 `.skill`，真正的 skill 名已经写在 `SKILL.md` 里：`resume-skill`。

### 2. 放入你的资料、照片、模板
(不懂的直接把自己简历资料包和照片发给agent让他搞定）

运行：

```powershell
python -m resume_skill init
```

然后把这些文件放好：

- `data/my_experiences.local.json`：你的经历资料库
- `data/my_profile.local.json`：姓名、电话、邮箱等
- `data/photo.png`：证件照或头像
- `templates/<模板名>/`：可选，自定义简历模板

### 3. 截图 JD，让 Agent 生成

发岗位jd截图后对 Agent 说：

```text
用 $resume-skill 根据这张 JD 截图做一份简历
```

生成结果会在 `resume_output_<时间>/`：

- `draft_resume.md`
- `resume.html`
- `resume.pdf`（如果电脑有 Chrome 或 Edge）
- `rendered_experiences.json`（实际写进一页简历的经历清单）

## 手动命令

JD 是文本文件：

```powershell
python -m resume_skill build jd.txt --pdf
```

JD 是图片，并且你配置了 `VISION_API_KEY`：

```powershell
python -m resume_skill build --image jd.jpg --pdf
```

指定资料、照片、模板：

```powershell
python -m resume_skill build jd.txt --experiences data/my_experiences.local.json --profile data/my_profile.local.json --photo data/photo.png --template classic_zh --pdf
```

默认会强制一页。只有你明确想看完整多页版本时才加：

```powershell
python -m resume_skill build jd.txt --pdf --allow-multipage
```

## 换模板
（不懂的直接把这一块复制给agent代劳）
把新模板放到：

```text
templates/my_template/template.html
templates/my_template/style.css
```

然后运行：

```powershell
python -m resume_skill build jd.txt --template my_template --pdf
```

模板里可以使用这些占位符：

```text
{{ style_css }}
{{ name }}
{{ title }}
{{ contact_html }}
{{ photo_html }}
{{ sections_html }}
{{ generated_at }}
{{ density_class }}
```

## 隐私

真实资料只放 `.local.json`，默认不会提交到仓库。这个工具只生成文件，不会自动投递简历。
