#!/usr/bin/env python3
"""Portable workspace scaffolder and validator for book-video-factory."""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
from pathlib import Path, PureWindowsPath


SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_ROOT = SKILL_ROOT / "assets" / "templates"
ACCOUNT_ID_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62})$")
WINDOWS_RESERVED_NAMES = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{number}" for number in range(1, 10)),
    *(f"lpt{number}" for number in range(1, 10)),
}
PATH_FIELDS = {
    "video.intro",
    "video.visual_theme",
    "audio.voice_reference",
    "audio.bgm",
    "artifacts.research",
    "artifacts.script",
    "artifacts.storyboard",
    "artifacts.images[]",
    "artifacts.voice",
    "artifacts.final_mix",
    "artifacts.transcript",
    "artifacts.preview",
    "artifacts.output",
}
WORKSPACE_REQUIRED_FIELDS = {
    "schema_version",
    "default_account",
    "providers.research",
    "providers.image",
    "providers.tts",
    "providers.transcription",
    "providers.audio_mix",
    "providers.renderer",
}
ACCOUNT_REQUIRED_FIELDS = {
    "schema_version", "account_id", "platform",
    "video.width", "video.height", "video.target_duration_seconds",
    "video.intro", "video.visual_theme", "video.opening.title_format",
    "video.intro_to_main_transition.type", "video.intro_to_main_transition.duration_seconds",
    "video.ending.fade_out", "audio.voice_reference", "audio.bgm",
    "audio.bgm_start_seconds", "audio.bgm_loop", "audio.duck_under_voice",
    "subtitles.title_uses_book_marks", "images.count", "images.default_style",
    "providers.research", "providers.image", "providers.tts",
    "providers.transcription", "providers.audio_mix", "providers.renderer",
    "workflow.require_script_approval", "workflow.require_image_approval",
    "workflow.require_preview_approval_before_render", "workflow.allow_social_publish",
}
BOOK_REQUIRED_FIELDS = {
    "schema_version", "book_id", "account_id", "title", "author",
    "versions.script", "versions.storyboard", "versions.images", "versions.audio",
    "versions.preview", "versions.output", "status.research", "status.script",
    "status.storyboard", "status.images", "status.voice", "status.preview",
    "status.output", "status.publish", "artifacts.research", "artifacts.script",
    "artifacts.storyboard", "artifacts.images", "artifacts.voice", "artifacts.final_mix",
    "artifacts.transcript", "artifacts.preview", "artifacts.output",
}
BOOLEAN_FIELDS = {
    "video.ending.fade_out", "audio.bgm_loop", "audio.duck_under_voice",
    "subtitles.title_uses_book_marks", "workflow.require_script_approval",
    "workflow.require_image_approval", "workflow.require_preview_approval_before_render",
    "workflow.allow_social_publish",
}
POSITIVE_INTEGER_FIELDS = {
    "video.width", "video.height", "video.target_duration_seconds", "images.count",
}
BOOK_DIRS = (
    "01-research",
    "02-script",
    "03-storyboard",
    "04-images",
    "05-audio",
    "06-transcript",
    "07-render",
    "08-preview",
    "09-output",
)
SHARED_DIRS = ("intro", "bgm", "voice-reference", "fonts", "config")
EXPORT_DIRS = ("ready", "published", "archive")

WORKSPACE_YAML = """schema_version: 1
default_account: ""
providers:
  research: auto
  image: auto
  tts: auto
  transcription: auto
  audio_mix: auto
  renderer: auto
"""

GITIGNORE = """*.tmp
__pycache__/
.DS_Store
Thumbs.db
.env.local
"""


class WorkspaceError(RuntimeError):
    pass


def write_new(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="") as handle:
            handle.write(content)
    except FileExistsError as exc:
        raise WorkspaceError(f"文件已存在，不会覆盖：{path}") from exc


def template_text(name: str, replacements: dict[str, str] | None = None) -> str:
    path = TEMPLATE_ROOT / name
    if not path.is_file():
        raise WorkspaceError(f"缺少模板：{name}")
    text = path.read_text(encoding="utf-8")
    for key, value in (replacements or {}).items():
        text = text.replace(key, value)
    return text


def valid_account_id(value: str) -> str:
    if not ACCOUNT_ID_RE.fullmatch(value):
        raise WorkspaceError("账号 ID 只能包含小写字母、数字和连字符，长度不超过 63。")
    if value.lower() in WINDOWS_RESERVED_NAMES:
        raise WorkspaceError(f"账号 ID 是 Windows 保留名称，不能跨平台使用：{value}")
    return value


def safe_slug(title: str) -> str:
    value = re.sub(r"[\\/\x00-\x1f<>:\"|?*]+", "-", title.strip())
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-. ")
    if not value or value in {".", ".."}:
        raise WorkspaceError("书名无法生成安全目录名。")
    return value[:80].rstrip("-. ")


def init_workspace(root: Path) -> dict[str, str]:
    if root.exists() and any(root.iterdir()):
        raise WorkspaceError(f"目标目录不是空目录，不会覆盖：{root}")
    root.mkdir(parents=True, exist_ok=True)
    (root / "accounts").mkdir()
    write_new(root / "workspace.yaml", WORKSPACE_YAML)
    write_new(root / ".env.local", "")
    write_new(root / ".gitignore", GITIGNORE)
    return {"workspace": str(root), "status": "created"}


def add_account(root: Path, account_id: str) -> dict[str, str]:
    valid_account_id(account_id)
    if not (root / "workspace.yaml").is_file():
        raise WorkspaceError("不是有效工作区：缺少 workspace.yaml。")
    account = root / "accounts" / account_id
    if account.exists():
        raise WorkspaceError(f"账号已存在，不会覆盖：{account_id}")
    for name in SHARED_DIRS:
        (account / "shared" / name).mkdir(parents=True, exist_ok=True)
    (account / "books").mkdir(parents=True)
    for name in EXPORT_DIRS:
        (account / "exports" / name).mkdir(parents=True, exist_ok=True)
    write_new(
        account / "account.yaml",
        template_text("account.yaml", {"__ACCOUNT_ID__": account_id}),
    )
    shutil.copyfile(TEMPLATE_ROOT / "production.csv", account / "production.csv")
    shutil.copyfile(TEMPLATE_ROOT / "visual-theme.css", account / "shared" / "config" / "visual-theme.css")
    return {"account": account_id, "status": "created"}


def next_book_id(books_dir: Path) -> str:
    values = []
    for child in books_dir.iterdir():
        match = re.match(r"^(\d{3})-", child.name) if child.is_dir() else None
        if match:
            values.append(int(match.group(1)))
    value = max(values, default=0) + 1
    if value > 999:
        raise WorkspaceError("三位书籍编号已用完，请归档账号或调整编号策略。")
    return f"{value:03d}"


def add_book(root: Path, account_id: str, title: str, author: str) -> dict[str, str]:
    valid_account_id(account_id)
    account = root / "accounts" / account_id
    books = account / "books"
    if not (account / "account.yaml").is_file() or not books.is_dir():
        raise WorkspaceError(f"账号不存在或结构不完整：{account_id}")
    title = title.strip()
    author = author.strip()
    if not title:
        raise WorkspaceError("书名不能为空。")
    slug = safe_slug(title)
    for child in books.iterdir():
        if child.is_dir() and child.name.partition("-")[2] == slug:
            raise WorkspaceError(f"同名书籍任务已存在，不会覆盖：{child.name}")
    book_id = next_book_id(books)
    book = books / f"{book_id}-{slug}"
    book.mkdir()
    for name in BOOK_DIRS:
        (book / name).mkdir()
    replacements = {
        "__BOOK_ID__": json.dumps(book_id, ensure_ascii=False),
        "__BOOK_TITLE__": json.dumps(title, ensure_ascii=False),
        "__BOOK_AUTHOR__": json.dumps(author, ensure_ascii=False),
        "__ACCOUNT_ID__": account_id,
    }
    write_new(book / "book.yaml", template_text("book.yaml", replacements))
    with (account / "production.csv").open("a", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerow(
            [book_id, title, author, "待开始", "待开始", "待开始", "待开始", "待开始", "待开始", "待开始", "未发布", ""]
        )
    return {"account": account_id, "book": book.name, "status": "created"}


def parse_scalar(raw: str, source: str, number: int) -> str:
    value = raw.strip()
    if not value:
        return ""
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise WorkspaceError(f"{source}:{number} 包含无效的双引号字符串") from exc
        return str(parsed)
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            raise WorkspaceError(f"{source}:{number} 包含未闭合的单引号字符串")
        return value[1:-1].replace("''", "'")
    if value.startswith(("{", "[")):
        try:
            json.loads(value)
        except json.JSONDecodeError as exc:
            raise WorkspaceError(f"{source}:{number} 包含无效的行内集合") from exc
        return value
    if " #" in value:
        value = value.split(" #", 1)[0].rstrip()
    return value


def yaml_scalars(config: Path, source: str) -> list[tuple[str, str, int]]:
    """Read the conservative YAML subset used by this skill's templates."""
    stack: list[tuple[int, str]] = []
    values: list[tuple[str, str, int]] = []
    for number, line in enumerate(config.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" in line[: len(line) - len(line.lstrip())]:
            raise WorkspaceError(f"{source}:{number} 使用了不支持的 Tab 缩进")
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if stripped.startswith("- "):
            if not stack:
                raise WorkspaceError(f"{source}:{number} 顶层列表不符合配置契约")
            path = ".".join(key for _, key in stack) + "[]"
            values.append((path, parse_scalar(stripped[2:], source, number), number))
            continue
        if ":" not in stripped:
            raise WorkspaceError(f"{source}:{number} 不是有效的键值行")
        key, raw = stripped.split(":", 1)
        key = key.strip()
        if not key:
            raise WorkspaceError(f"{source}:{number} 缺少字段名")
        path = ".".join([*(item[1] for item in stack), key])
        if raw.strip():
            values.append((path, parse_scalar(raw, source, number), number))
        else:
            stack.append((indent, key))
    return values


def looks_absolute(value: str) -> bool:
    if not value or value.startswith(("http://", "https://")):
        return False
    return Path(value).is_absolute() or PureWindowsPath(value).is_absolute() or value.startswith("\\\\")


def escapes_parent(value: str) -> bool:
    if not value or value.startswith(("http://", "https://")):
        return False
    return ".." in Path(value).parts or ".." in PureWindowsPath(value).parts


def gitignore_protects_env(text: str) -> bool:
    rules = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    protected_at = max((index for index, rule in enumerate(rules) if rule in {".env.local", "/.env.local"}), default=-1)
    if protected_at < 0:
        return False
    return not any(rule.startswith("!") for rule in rules[protected_at + 1 :])


def is_inside(path: Path, base: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(base.resolve(strict=False))
        return True
    except ValueError:
        return False


def validate_schema(config: Path, root: Path, values: list[tuple[str, str, int]], errors: list[str]) -> None:
    relative = config.relative_to(root)
    fields = {field: value for field, value, _ in values}
    if relative == Path("workspace.yaml"):
        required = WORKSPACE_REQUIRED_FIELDS
        kind = "workspace"
    elif config.name == "account.yaml":
        required = ACCOUNT_REQUIRED_FIELDS
        kind = "account"
    elif config.name == "book.yaml":
        required = BOOK_REQUIRED_FIELDS
        kind = "book"
    else:
        return
    missing = sorted(required - fields.keys())
    if missing:
        errors.append(f"{relative} 缺少必需字段：{', '.join(missing)}")
        return
    if fields.get("schema_version") != "1":
        errors.append(f"{relative} 的 schema_version 必须为 1")
    for field in sorted(BOOLEAN_FIELDS & fields.keys()):
        if fields[field].lower() not in {"true", "false"}:
            errors.append(f"{relative} 的 {field} 必须为 true 或 false")
    for field in sorted(POSITIVE_INTEGER_FIELDS & fields.keys()):
        try:
            valid = int(fields[field]) > 0
        except ValueError:
            valid = False
        if not valid:
            errors.append(f"{relative} 的 {field} 必须为正整数")
    if kind == "account":
        if fields.get("account_id") != config.parent.name:
            errors.append(f"{relative} 的 account_id 必须与账号目录名一致")
        if "{book_title}" not in fields.get("video.opening.title_format", ""):
            errors.append(f"{relative} 的 video.opening.title_format 必须包含 {{book_title}}")
    elif kind == "book":
        expected_account = config.parent.parent.parent.name
        expected_book = config.parent.name.partition("-")[0]
        if fields.get("account_id") != expected_account:
            errors.append(f"{relative} 的 account_id 必须与所属账号目录名一致")
        if fields.get("book_id") != expected_book:
            errors.append(f"{relative} 的 book_id 必须与书籍目录编号一致")
        if not fields.get("title"):
            errors.append(f"{relative} 的 title 不能为空")


def validate_config_paths(config: Path, root: Path, errors: list[str], warnings: list[str]) -> None:
    relative = config.relative_to(root)
    if config.is_symlink() or not is_inside(config, root):
        errors.append(f"{relative} 不能通过符号链接指向工作区外")
        return
    try:
        values = yaml_scalars(config, str(relative))
    except (OSError, UnicodeError, WorkspaceError) as exc:
        errors.append(str(exc))
        return
    validate_schema(config, root, values, errors)
    base = config.parent
    for field, value, number in values:
        if field not in PATH_FIELDS or not value:
            continue
        if looks_absolute(value):
            errors.append(f"{relative}:{number} 的 {field} 含绝对路径")
            continue
        if escapes_parent(value):
            errors.append(f"{relative}:{number} 的 {field} 含父目录逃逸")
            continue
        candidate = base / value
        if not is_inside(candidate, base) or not is_inside(candidate, root):
            errors.append(f"{relative}:{number} 的 {field} 通过符号链接逃出所属目录")
            continue
        if not candidate.exists():
            warnings.append(f"{relative}:{number} 的 {field} 指向不存在的素材：{value}")


def validate(root: Path) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    config_paths: list[Path] = []
    for name in ("workspace.yaml", ".gitignore", "accounts"):
        if not (root / name).exists():
            errors.append(f"工作区缺少：{name}")
    gitignore = root / ".gitignore"
    if gitignore.is_file() and not gitignore_protects_env(gitignore.read_text(encoding="utf-8")):
        errors.append(".gitignore 未有效忽略 .env.local")
    workspace_config = root / "workspace.yaml"
    if workspace_config.is_file():
        config_paths.append(workspace_config)
    accounts_dir = root / "accounts"
    if accounts_dir.is_dir():
        for account in sorted(path for path in accounts_dir.iterdir() if path.is_dir()):
            try:
                valid_account_id(account.name)
            except WorkspaceError as exc:
                errors.append(str(exc))
            for name in ("account.yaml", "production.csv", "shared", "books", "exports"):
                if not (account / name).exists():
                    errors.append(f"账号 {account.name} 缺少：{name}")
            account_config = account / "account.yaml"
            if account_config.is_file():
                config_paths.append(account_config)
            for name in SHARED_DIRS:
                if not (account / "shared" / name).is_dir():
                    errors.append(f"账号 {account.name} 缺少共享目录：{name}")
            for name in EXPORT_DIRS:
                if not (account / "exports" / name).is_dir():
                    errors.append(f"账号 {account.name} 缺少导出目录：{name}")
            books_dir = account / "books"
            if books_dir.is_dir():
                for book in sorted(path for path in books_dir.iterdir() if path.is_dir()):
                    if not re.match(r"^\d{3}-.+", book.name):
                        errors.append(f"非法书籍目录名：{book.name}")
                    if not (book / "book.yaml").is_file():
                        errors.append(f"书籍 {book.name} 缺少 book.yaml")
                    else:
                        config_paths.append(book / "book.yaml")
                    for name in BOOK_DIRS:
                        if not (book / name).is_dir():
                            errors.append(f"书籍 {book.name} 缺少阶段目录：{name}")
    for config in config_paths:
        validate_config_paths(config, root, errors, warnings)
    if not (root / ".env.local").exists():
        warnings.append("未创建 .env.local；需要密钥时再创建即可")
    return {"ok": not errors, "errors": errors, "warnings": warnings}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="管理通用图书短视频工作区")
    sub = result.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="初始化工作区")
    init.add_argument("--root", default="book-video-workspace")
    account = sub.add_parser("add-account", help="添加账号")
    account.add_argument("--root", default="book-video-workspace")
    account.add_argument("--id", required=True)
    book = sub.add_parser("add-book", help="添加单书任务")
    book.add_argument("--root", default="book-video-workspace")
    book.add_argument("--account", required=True)
    book.add_argument("--title", required=True)
    book.add_argument("--author", default="")
    check = sub.add_parser("validate", help="校验工作区")
    check.add_argument("--root", default="book-video-workspace")
    return result


def main() -> int:
    args = parser().parse_args()
    root = Path(args.root).expanduser()
    try:
        if args.command == "init":
            result = init_workspace(root)
        elif args.command == "add-account":
            result = add_account(root, args.id)
        elif args.command == "add-book":
            result = add_book(root, args.account, args.title, args.author)
        else:
            result = validate(root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok", True) else 1
    except (OSError, WorkspaceError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
