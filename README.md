# resume-skill

JD 截图进来，匹配你的本地资料库，生成一份适合岗位的中文简历。

默认 PDF 必须压缩成 1 页。内容过多时，系统会优先保留最匹配 JD 的经历和结果数据，主动删掉低相关内容。

## 3 步开始

### 1. 安装 Skill

把这个链接https://github.com/wangzichang224-design/One-Job-One-Resume/  丢给codingagent，让agent安装就好

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
- 

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
