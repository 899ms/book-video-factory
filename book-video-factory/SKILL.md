---
name: book-video-factory
description: 通用的多账号图书短视频生产工作流。用于用户希望建立图书号项目目录、配置账号级片头/声音/BGM/视觉规范，或只提供一本书后依次完成资料研究、口播稿、分镜、图片、配音、字幕、预览与成片导出。适用于新建工作区、批量管理多个账号、继续已有单书任务和检查生产状态；不绑定特定研究、图片、TTS、转录或视频渲染供应商。
---

# 图书号视频工厂

把一次性的视频制作变成可移动、可复用的账号矩阵工作区。第一次沉淀账号配置；以后以“账号 + 一本书”为入口推进单书生产。

## 不可违反的规则

- 所有写入配置的素材路径必须相对于账号目录。不得把绝对路径写入 `workspace.yaml`、`account.yaml`、`book.yaml`、日志或导出清单。
- API Key 只从进程环境或工作区 `.env.local` 读取；不得回显、复制到模板或提交到版本库。
- 不捆绑字体、音乐、视频、参考声音或账号凭据。只创建空素材目录。
- 先检查当前 Agent 实际拥有的工具。不得假装某阶段已经完成，也不得擅自安装大型依赖、下载模型或调用付费接口。
- 默认在文案、图片、预览三个节点等待确认。不得自动发布到社交平台。
- 书籍内容以事实摘要、观点提炼和原创表达为主，不复制大段原文。提醒用户只使用有权使用的声音、字体、图片、音乐与视频。

## 入口判断

1. 用户指定工作区时使用其指定位置；否则使用当前项目下的 `book-video-workspace`。
2. 若工作区不存在，进入“首次初始化”。
3. 若工作区存在但账号不明确：只有一个账号时使用它；多个账号时询问目标账号。
4. 用户给出书名后进入“单书生产”；用户只要求规划目录、增加账号或检查状态时，只完成对应管理任务。
5. 已存在的配置不要重复询问。只询问会改变结果且无法从文件或工具发现的信息。

## 工作区契约

即使模板或脚本不可用，也必须能按下面的结构直接创建：

```text
book-video-workspace/
├── workspace.yaml
├── .env.local
├── .gitignore
└── accounts/
    └── <account-id>/
        ├── account.yaml
        ├── production.csv
        ├── shared/
        │   ├── intro/
        │   ├── bgm/
        │   ├── voice-reference/
        │   ├── fonts/
        │   └── config/visual-theme.css
        ├── books/
        │   └── <book-id>-<book-slug>/
        │       ├── book.yaml
        │       ├── 01-research/
        │       ├── 02-script/
        │       ├── 03-storyboard/
        │       ├── 04-images/
        │       ├── 05-audio/
        │       ├── 06-transcript/
        │       ├── 07-render/
        │       ├── 08-preview/
        │       └── 09-output/
        └── exports/
            ├── ready/
            ├── published/
            └── archive/
```

最小账号配置必须覆盖这些边界：

```yaml
account_id: account-01
platform: xiaohongshu
video:
  width: 1080
  height: 1920
  target_duration_seconds: 40
  intro: ""
  opening:
    title_format: "《{book_title}》"
  intro_to_main_transition:
    type: glitch
    duration_seconds: 0.35
audio:
  voice_reference: ""
  bgm: ""
  bgm_start_seconds: 0
  bgm_loop: true
images: {count: 4, default_style: healing-watercolor-storybook}
workflow:
  require_script_approval: true
  require_image_approval: true
  require_preview_approval_before_render: true
```

空字符串表示尚未配置素材。素材存在时写相对路径，例如 `shared/bgm/default-bgm.mp3`。详细字段见 [账号配置](references/account-config.md)，完整目录职责见 [项目结构](references/project-layout.md)。

## 配置优先级

发生冲突时严格按以下顺序取值：

1. 当前对话中用户明确提出的新要求。
2. 本书 `book.yaml` 的临时覆盖项。
3. 账号 `account.yaml` 的长期规则。
4. 工作区 `workspace.yaml` 的工具选择。
5. 本 Skill 的通用默认值。

用户确认某项以后都要沿用时，更新账号配置；只影响当前书时，写入 `book.yaml`。不要把账号固定项散落在渲染场景中。

## 首次初始化

1. 创建工作区和 `.gitignore`，确保 `.env.local` 被忽略。
2. 创建账号 ID；ID 只使用小写字母、数字和连字符。
3. 收集并保存账号长期规则：平台、画幅、目标时长、片头、标题、转场、声音、BGM、字幕、图片风格和确认节点。
4. 把用户提供的共享素材复制到相应 `shared/` 目录，再在配置中记录相对路径；不要链接到工作区外文件。
5. 检查研究、图片、TTS、转录、混音和渲染能力，把选择写入 `workspace.yaml` 或 `account.yaml`。缺失能力允许暂时标记为 `auto`。
6. 运行工作区校验；报告错误和不阻塞生产的警告。

如果 Python 可用，可从 Skill 根目录运行可选脚本：

```bash
python scripts/workspace.py init --root ./book-video-workspace
python scripts/workspace.py add-account --root ./book-video-workspace --id account-01
python scripts/workspace.py validate --root ./book-video-workspace
```

没有 Python 时直接用文件工具创建相同结构，不得把 Python 当作核心依赖。

## 单书生产

### 1. 建立任务

- 接收目标账号、书名和作者；作者未知时允许留空，但研究阶段要核实。
- 创建递增三位编号和安全目录名，生成 `book.yaml`，在 `production.csv` 新增一行。
- 若同一账号已存在同名书，继续已有任务，不覆盖文件；除非用户明确要求创建新版本。

可选脚本：

```bash
python scripts/workspace.py add-book --root ./book-video-workspace --account account-01 --title "书名" --author "作者"
```

### 2. 研究与文案

- 优先使用已配置的读书或搜索工具；也可以使用用户提供的书摘、笔记和资料。
- 把来源、事实摘要和资料缺口写入 `01-research/sources.md`。
- 围绕一个适合短视频传播的角度写自然口播，不强行概括全书，不编造名言、销量或评价。
- 保存 `02-script/script-v1.md`，报告传播角度和预计时长。
- 若 `require_script_approval` 为真，在这里停止并等待确认。

### 3. 分镜与图片

- 按口播含义拆分字幕和 3–4 个画面段落，切换点放在断句边界。
- 保存 `03-storyboard/storyboard-v1.yaml`，其中每个画面包含旁白范围、构图、情绪、提示词和字幕安全区。
- 图片只做背景与情绪隐喻，不生成书名、作者、字幕、Logo、水印或平台 UI。
- 使用同一视觉语言生成图片，保存为 `04-images/scene-01.*` 等稳定文件名。
- 若 `require_image_approval` 为真，展示图片并等待确认。

### 4. 音频、字幕与渲染工程

- 按能力发现选择 TTS 或用户录音，完整旁白优先一次生成，保存 `05-audio/voice-v1.wav`。
- BGM 从账号配置指定时间进入；不足时按配置循环。BGM 必须低于旁白，优先做 ducking。
- 最终混音保存为 `05-audio/mix-final-v1.wav`。没有混音能力时明确停止，不输出伪成品。
- 用最终旁白或最终混音转录，修正识别错误后保存 `06-transcript/final.zh-CN.srt`；其他语言字幕按账号配置生成。
- 在 `07-render/<renderer>/` 创建渲染工程。标题用 HTML/图层叠加并服从 `title_format`，不要把文字烘焙进背景图。
- 图片切换和字幕时间必须来自最终音频，不靠平均分配。

### 5. 预览、导出与状态

- 生成低成本预览到 `08-preview/preview-v1.mp4` 或提供渲染器的可访问预览入口。
- 若 `require_preview_approval_before_render` 为真，等待用户确认后才正式渲染。
- 正式成片写入 `09-output/final-v1.mp4`，并复制到账号 `exports/ready/`。
- 更新 `book.yaml` 和 `production.csv`。Skill 不负责上传或发布；用户发布后才将文件归档到 `published/` 并填写发布日期。

完整状态和文件命名约定见 [生产流程](references/production-workflow.md)。

## 工具适配规则

按“能力”选择工具，不按品牌写死流程：

| 阶段 | 所需能力 | 允许实现 |
|---|---|---|
| 研究 | 书籍资料检索 | 读书工具、网页搜索、用户资料 |
| 图片 | 文生图或图像处理 | 当前 Agent 可调用的图片工具 |
| 口播 | TTS、声音克隆或录音 | 本地模型、云端 TTS、用户音频 |
| 字幕 | 音频转文字 | Whisper 类工具或渲染器转录 |
| 混音 | 循环、ducking、响度 | FFmpeg 或渲染器内置音频能力 |
| 视频 | 时间线合成与渲染 | HyperFrames 或其他可用渲染器 |

选择前先检查工具、认证和成本。调用会上传用户文件或产生费用时，先获得用户确认。具体输入输出契约和降级方式见 [工具适配](references/provider-adapters.md)。

## 校验

在预览和导出前检查：

- 配置中的本地素材引用均为相对路径，且没有 `..` 逃逸账号目录。
- `.env.local` 已被忽略，输出中没有密钥。
- 文案和图片已满足启用的确认节点。
- 最终音频、字幕和切图时间属于同一版本。
- 标题带规范书名号，背景图没有文字。
- 缺失工具或素材被明确报告，没有伪造完成状态。
- `book.yaml` 与 `production.csv` 状态一致。
- 正式渲染前已满足预览确认规则。

如果 Python 可用，运行：

```bash
python scripts/workspace.py validate --root ./book-video-workspace
```

## 按需读取

- 新建、移动或审计目录时读 [项目结构](references/project-layout.md)。
- 编辑账号字段、覆盖规则或素材引用时读 [账号配置](references/account-config.md)。
- 选择研究、图片、TTS、转录、混音或渲染工具时读 [工具适配](references/provider-adapters.md)。
- 推进单书状态、命名产物或恢复中断任务时读 [生产流程](references/production-workflow.md)。
