# 账号配置

## 配置分层

| 文件 | 负责内容 |
|---|---|
| `workspace.yaml` | 可用工具、工作区默认供应商 |
| `account.yaml` | 账号长期视觉、声音、片头和审核规则 |
| `book.yaml` | 当前书籍信息、临时覆盖、版本和状态 |

优先级：当前对话要求 > `book.yaml` > `account.yaml` > `workspace.yaml` > Skill 默认值。

## 路径规则

素材字段允许为空或填写账号内相对路径：

```yaml
video:
  intro: shared/intro/default-intro.mp4
audio:
  bgm: shared/bgm/default-bgm.mp3
  voice_reference: shared/voice-reference/default-voice.wav
```

不得填写绝对路径或 `..`。用户从工作区外提供素材时，先复制到对应的 `shared/` 目录，再更新配置。

## 核心字段

### video

- `width`、`height`：默认 1080×1920。
- `target_duration_seconds`：目标而非强制截断点，默认 40 秒。
- `intro`：可为空的账号片头相对路径。
- `visual_theme`：账号视觉变量 CSS。
- `opening`：开场第一句、书名出现位置、标题格式与语速倾向。
- `intro_to_main_transition`：片头到正片的转场。
- `ending.fade_out`：是否允许结尾画面或音频淡出。

### audio

- `voice_reference`：可为空的参考声音相对路径。
- `tts.provider/options`：供应商名和非敏感参数；密钥不能写这里。
- `bgm`、`bgm_start_seconds`、`bgm_loop`：BGM 素材和时间行为。
- `duck_under_voice`：旁白出现时是否自动压低 BGM。
- `mix`：片头原声、旁白、BGM、响度与峰值目标。

### subtitles、images、providers

- `subtitles.languages`：以最终音频生成的字幕语言。
- `title_uses_book_marks`：中文标题是否使用书名号。
- `images.count/default_style`：默认图片数量和统一视觉语言。
- `providers`：研究、图片、TTS、转录、混音、渲染能力；`auto` 表示运行时检测。

### workflow

- `require_script_approval`：文案确认后才生成图片。
- `require_image_approval`：图片确认后才生成最终音视频工程。
- `require_preview_approval_before_render`：预览确认后才正式导出。
- `allow_social_publish`：公开模板固定为 `false`；发布由用户完成。

## 修改归属

- “以后这个账号都这样”：写入 `account.yaml`。
- “只有这本书这样”：写入 `book.yaml.overrides`。
- “这台工作区优先用某工具”：写入 `workspace.yaml.providers`。
- 密钥、令牌、Cookie：只放环境或 `.env.local`。
