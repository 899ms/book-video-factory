# 生产流程

## 状态机

每个阶段只使用以下状态：

- `pending`：尚未开始。
- `in_progress`：正在制作。
- `needs_review`：等待用户确认。
- `approved`：用户已确认。
- `completed`：阶段产物完成且通过必要校验。
- `blocked`：缺工具、素材或必要输入。
- `failed`：执行失败并留有错误说明。

发布状态单独使用 `unpublished`、`published`、`archived`。

## 阶段推进

1. `research` 完成后才能形成事实型口播。
2. `script` 在启用确认时必须经过 `needs_review → approved`。
3. `storyboard` 基于已确认文案；图片变更要同步检查分镜。
4. `images` 在启用确认时必须经过 `needs_review → approved`。
5. `voice` 只能使用已确认文案版本。
6. `transcript`、字幕和切图时间只能来自最终音频版本。
7. `preview` 通过校验后进入 `needs_review`。
8. `output` 只有在预览确认或确认开关关闭时才能开始。

中断后先读 `book.yaml.status`、`versions` 和 `artifacts`，从最后一个未完成阶段继续，不重做已确认产物。

## 推荐文件名

```text
01-research/sources.md
02-script/script-v1.md
03-storyboard/storyboard-v1.yaml
04-images/scene-01.png
05-audio/voice-v1.wav
05-audio/mix-final-v1.wav
06-transcript/final.zh-CN.srt
08-preview/preview-v1.mp4
09-output/final-v1.mp4
```

修改内容时递增相应版本；不要原地覆盖用户已经确认的版本。

## production.csv 同步

CSV 列固定为：

```text
编号,书名,作者,研究,文案,分镜,图片,配音,预览,导出,发布,发布日期
```

- `book.yaml` 是单书状态真相源，CSV 是账号总览。
- 阶段状态变化后同步对应单元格。
- 发布日期使用 `YYYY-MM-DD`，未发布时留空。
- 自动化不得把 `待确认` 写成 `完成`。

## 预览验收

- 开场、书名出现位置和转场服从账号配置。
- 顶部标题格式一致，中文书名默认带 `《》`。
- 图片无文字，主体不被标题和字幕遮挡。
- 口播清楚，BGM 不抢人声；循环处无明显断裂。
- 字幕、切图点和最终音频属于同一版本。
- 结尾是否淡出服从账号配置。
- 启用的文案、图片和预览确认节点都有记录。

## 导出边界

- 成片先写入单书 `09-output`，再复制到账号 `exports/ready`。
- Skill 不登录账号、不上传、不点击发布。
- 用户确认已经发布后，才移动到 `exports/published` 并更新日期。
