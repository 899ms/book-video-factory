# 图书号视频工厂

一个通用、可移植的多账号图书短视频生产 Skill。

第一次使用时建立账号配置，沉淀片头、声音、BGM、视觉风格和确认规则；后续只需提供目标账号与一本书，即可按统一目录推进资料研究、口播稿、分镜、图片、配音、字幕、预览和成片导出。

## 效果演示

下面是一段约 10 秒的成片演示，包含统一片头、书名展示、转场、口播和字幕效果。

https://github.com/user-attachments/assets/48d0a163-9bbc-4763-b10d-c734549dd74b

## 特点

- 一个工作区管理多个图书账号
- 账号共享素材与单书生产文件分离
- 文案、图片、预览三个可配置的人工确认节点
- 不绑定微信读书、VoxCPM、Whisper、HyperFrames 等具体供应商
- 所有素材引用使用相对路径，工作区可以整体移动
- 不自动安装大型依赖、不自动调用付费接口、不自动发布

## 安装

仓库中的 [`book-video-factory`](book-video-factory/) 目录是完整 Skill。

将该目录安装或复制到你的 Agent 所使用的 Skills 目录，然后通过下面的方式调用：

```text
使用 $book-video-factory 帮我创建一个图书号视频工作区。
```

也可以直接下载 [`dist/book-video-factory-redskill.zip`](dist/book-video-factory-redskill.zip)，用于支持 ZIP 导入的 Skill 平台。

## 使用示例

首次配置账号：

```text
帮我创建一个图书号视频工作区，并配置第一个账号。
```

制作一本书：

```text
用 account-01 给《书名》做一条 40 秒左右的竖屏图书视频。
```

恢复中断任务：

```text
检查这个图书视频工作区的进度，继续上次没有完成的书。
```

## 工具依赖

微信读书不是必需依赖。Skill 会根据当前 Agent 的实际能力选择研究、图片、TTS、转录、混音和渲染工具。

没有相应工具时，可以改用网页资料、用户提供的书摘、现成图片或录音；无法完成某个阶段时会明确停止，不会伪造产物。

Python 脚本同样是可选加速器。没有 Python 时，Agent 仍可根据 `SKILL.md` 中的工作区契约直接创建目录。

## 隐私与素材

Skill 包和可下载 ZIP 不包含：

- 片头视频、BGM、参考声音、字体或图片
- 账号密码、Cookie、API Key 或 Token
- 作者电脑的本地路径或私人项目数据

README 中的公开演示视频只用于展示成片效果，不作为 Skill 素材分发。

使用者需要自行提供拥有合法使用权的声音、字体、图片、音乐和视频素材。

## 目录

```text
.
├── README.md
├── book-video-factory/
│   ├── SKILL.md
│   ├── agents/
│   ├── assets/templates/
│   ├── references/
│   └── scripts/
└── dist/
    └── book-video-factory-redskill.zip
```
