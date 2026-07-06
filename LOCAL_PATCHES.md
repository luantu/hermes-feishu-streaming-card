# 本地修订清单

本文档记录本地分支相对上游分支的全部修订，合并时对照此清单确保不丢失。

## 功能改动

### 1. GIF 动画 footer（server.py + render.py + feishu_client.py）

**server.py：**
- `UPLOADED_GIF_IMG_KEYS_KEY` AppKey
- `RESEND_AFTER_SECONDS_KEY` AppKey
- `_ensure_logger()` — 日志初始化
- `create_app()` 中 `_ensure_logger()` 调用 + `app[UPLOADED_GIF_IMG_KEYS_KEY] = {}` 初始化
- `create_app()` 中 GIF 启动上传（`on_startup` → `asyncio.create_task`）
- `_render_session_card()` 中 `loading_gif_img_key = _resolve_gif_img_key(request.app, session)` 并向 `render_card()` 传递
- `_resolve_gif_img_key()` 函数

**render.py：**
- `render_card()` 接受 `loading_gif_img_key: str | None = None` 参数
- `_render_footer()` 接受 `loading_gif_img_key: str | None = None`，非 completed 状态优先用 GIF
- `_render_thinking_footer_gif()` 函数 — 返回 custom_icon markdown 元素
- footer 是 list 时 `elements.extend(footer)` 而非 `append`

**feishu_client.py：**
- `upload_image()` 方法
- `FormData` import

### 2. 话题消息禁用（server.py）

- `_thread_id_for_event()` → `return None`
- `_reply_to_message_id_for_event()` → `return None`

### 3. tool_summary 配置化（render.py）

- `DEFAULT_FOOTER_FIELDS` 中增加 `"tool_summary"`
- `render_card()` 中 `effective_fields` 计算、`show_tool_summary` 判断
- `_render_footer()` 中 `if field == "tool_summary": continue` 跳过
- 条件渲染：`if not timeline_elements and show_tool_summary:`

### 4. model 空值不显示（render.py）

- `_render_footer()`：`"Unknown"` → `""`

### 5. thinking 内容用文字（render.py）

- `render_card()`：`primary_text = "生成中..."` 替代 `_spinner_frame()`

### 6. 队列完成抑制修复（hook_runtime.py）

- `_event_was_delivered()` 函数：终态事件 `applied=False` 时仍视为已投递
- `emit_from_hermes_locals_async()` 使用 `_event_was_delivered(result, event_name)`
- `_event_was_applied()` 保留（其他路径仍用）

### 7. 并发消息不覆盖（server.py）

- `_apply_event_locked()` 中：`not applied and session.status in {"completed", "failed"} and event.event in TERMINAL_EVENTS` → 发新卡片

### 8. 长会话重发（多文件）

- `config.py`：`resend_after_seconds: 60`
- `server.py`：`RESEND_AFTER_SECONDS_KEY` + `_delete_and_resend` 逻辑
- `session.py`：`started_at` + `elapsed` property
- `metrics.py`：`feishu_delete_attempts/successes/failures`、`feishu_resend_attempts/successes/failures/fallbacks`

### 9. delete_message API（feishu_client.py + runner.py）

- `FeishuClient.delete_message()`
- `NoopFeishuClient.delete_message()`

### 10. cron deliver 优先级（hook_runtime.py）

- `build_cron_event()`：`"origin"`/`"none"` 不作为平台名，优先用 resolved targets

## 日志改动

### 11. sidecar 日志（server.py）

- `_ensure_logger()` — `StreamHandler` + `INFO` 级别
- `_log_handler_configured` 全局标志

### 12. PYTHONUNBUFFERED（process.py）

- `start_sidecar()`：`env={**os.environ, "PYTHONUNBUFFERED": "1"}`

### 13. hook 侧诊断日志（hook_runtime.py）

所有 `print(file=sys.stderr)` 调用：
- `emit_from_hermes_locals` / `_async` / `_threadsafe` 失败路径
- `emit_cron_delivery` 失败路径
- `should_suppress_native_response` 决策（含平台、delivered、附件）
- `_build_event` 返回 None 的各种原因
- `import sys` 新增

### 14. 附件 is_media 标记（hook_runtime.py）

- `_has_media_attachments()`：精确检查 `is_media` 字段
- `_extract_attachments()`：`MEDIA_RE` 匹配项标记 `is_media: True`，`LOCAL_FILE_RE` 不加标记
- `_coerce_attachment()`：添加 `is_media: True`

## 其他改动

### 15. patcher 缩进修复（patcher.py）

- `_render_complete_hook_block` 和 `_render_queued_complete_hook_block` 中 3 行缩进从 deeper_indent 改为 inner_indent

### 16. reply_to_message_id 移除（hook_runtime.py）

- `_event_data()` 中不发送 `reply_to_message_id` 字段（配合话题禁用）

### 17. 资源文件

- `assets/loading.gif` — GIF 动画素材
- `config.yaml.example` — tool_summary 配置说明
- `AGENTS.md` — 本地开发指南
- `restart` / `back-restart` / `update` — 运维脚本
- `SCRIPT_OPTIMIZATION.md` — 脚本优化文档
- `.gitignore` — 新增 `.claude/` `.codegraph/` `.agents/` `uv.lock`
