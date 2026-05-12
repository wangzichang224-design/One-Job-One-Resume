# 安装

## Codex

1. 把 `resume-skill` 文件夹复制到：

```text
C:\Users\<你>\.codex\skills\resume-skill
```

2. 进入这个文件夹，安装命令：

```powershell
python -m pip install -e .
```

3. 重启 Codex，然后说：

```text
用 $resume-skill 根据这张 JD 截图做一份简历
```

## Claude

1. 把 `resume-skill` 文件夹复制到：

```text
C:\Users\<你>\.claude\skills\resume-skill
```

2. 进入这个文件夹，安装命令：

```powershell
python -m pip install -e .
```

3. 重启 Claude，然后说：

```text
用 $resume-skill 根据这张 JD 截图做一份简历
```

## 其他 Agent

把整个 `resume-skill` 文件夹放进它支持的 skills 或 plugins 目录，再运行：

```powershell
python -m pip install -e .
python -m resume_skill init
```

之后把资料放进 `data/`，把模板放进 `templates/`，日常只需要发 JD 截图。
