# 本地修订清单

本文档记录本地分支相对于上游（`upstream/main`）的全部修订。
每次合并上游后对比此清单确保不丢失。

> 最后更新：V4.0.4 合并后

---

## 一、render.py（15 项）

### 1.1 GIF 动画 footer
- `render_card()` 接受 `loading_gif_img_key: str | None = None` 参数
- `_render_footer()` 接受 `loading_gif_img_key` 参数，非 completed 状态优先用 GIF
- `_render_thinking_footer_gif()` 函数：返回 `custom_icon` markdown 元素
- footer 是 list 时 `elements.extend(footer)` 而非 `append`
- 代码位置：`render_card` 参数 → `_render_footer` → `_render_thinking_footer_gif`

### 1.2 tool_summary 配置化
- `DEFAULT_FOOTER_FIELDS` 中增加 `"tool_summary"`
- `render_card()` 中 `effective_fields` 计算、`show_tool_summary` 判断
- 条件渲染：`if not timeline_elements and show_tool_summary:`
- `_render_footer()` 中 `if field == "tool_summary": continue` 跳过内联

### 1.3 model 空值不显示
- `_render_footer()`：`"Unknown"` → `""`

### 1.4 thinking 内容用文字
- `primary_text = "生成中..."` 替代 `_spinner_frame()`

### 1.5 notice 卡片极简样式
- `session.delivery_kind == "notice"` 时早期返回极简卡片：
  - 无 title，无 footer，无 divider
  - 正文 `text_size: "x-small"`
  - header 只有颜色条（`_notice_template(level)`）

### 1.6 表格截断移除
- `_render_main_content_elements()` 中移除"内容含超过5个表格，超出部分已省略"截断逻辑

### 1.7 多表格分卡（`render_cards`）
- `render_cards()` 函数：超过 5 个表格时拆分内容为多张卡片
- `_split_content_by_tables()` 辅助函数
- 导入：`_markdown_structure_blocks, TABLE_SEPARATOR_RE, MAX_CARD_TABLES, count_markdown_tables`

### 1.8 完成状态 subtitle 显示正文摘要
- `_render_status()`：completed 时 subtitle 不再固定 "已完成"，而是 `session.answer_text`
- 飞书客户端渲染为 1 行 + 省略号

---

## 二、server.py（12 项）

### 2.1 GIF 上传支持
- `UPLOADED_GIF_IMG_KEYS_KEY` AppKey
- `RESEND_AFTER_SECONDS_KEY` AppKey
- `create_app()` 中 `app[UPLOADED_GIF_IMG_KEYS_KEY] = {}` 初始化
- `create_app()` 中 GIF 启动上传（`on_startup` → `asyncio.create_task`，含 15 秒超时）
- `_resolve_gif_img_key()` 函数（从缓存读 GIF key）
- `_render_session_card_for_app()` 中 `loading_gif_img_key` 传递给 `render_card()`

### 2.2 话题消息禁用
- `_thread_id_for_event()` → `return None`
- `_reply_to_message_id_for_event()`：只返回显式 `reply_to_message_id`（`om_` 开头），不自动推导

### 2.3 sidecar 日志
- `_ensure_logger()` 函数：`StreamHandler` + `INFO` 级别
- `_log_handler_configured` 全局标志
- `create_app()` 中 `_ensure_logger()` 调用

### 2.4 超时会话重发
- `RESEND_AFTER_SECONDS_KEY` 初始化（从 `card.resend_after_seconds` 读取，默认 60s）
- `_delete_and_resend()` 函数：撤回原卡片 → 发新卡片
- `_render_and_update()` 中：终态事件时检查 `session.elapsed >= resend_threshold`

### 2.5 timeline 动态展开
- `timeline_expanded` 默认值：`session.status not in {"completed", "failed"}`
- 流式中展开，完成后折叠

### 2.6 多表格分卡发送
- `_render_session_cards()` 函数：调用 `render_cards()` 获取多卡片列表
- `_render_and_update()` 中：终态事件更新成功后发送额外卡片

### 2.7 回复消息支持
- `_reply_to_message_id_for_event()`：返回事件数据中的显式 `reply_to_message_id`

---

## 三、hook_runtime.py（5 项）

### 3.1 队列完成抑制修复
- `_event_was_delivered()` 函数：终态事件 `applied=False` 时仍视为已投递
- `emit_from_hermes_locals_async()` 使用 `_event_was_delivered(result, event_name)`

### 3.2 notice 分类过滤
- heartbeat（`⏳ working`）→ 返回 `None`（不渲染卡片）
- self-improvement review → 返回 `None`
- 新增 gateway shutting down / restart 分类（`"网关状态"`, `level: "warning"`）

### 3.3 日志
- 所有 emit 失败路径、`should_suppress_native_response` 决策、`_build_event` 返回 None 原因都有 `print(file=sys.stderr)` 日志

---

## 四、session.py（3 项）

### 4.1 model 空值
- `model: str = ""`（类默认值）
- `session.apply()` 中 model fallback 从 `"Unknown"` 改为 `""`

### 4.2 回复消息 ID 只在显式时赋值
- `session.apply()` 中 `message.completed` 处理：移除 `elif event.message_id.startswith("om_"): self.reply_to_message_id = event.message_id` fallback
- 只有事件数据中有显式 `reply_to_message_id` 时才赋值

### 4.3 keep notice fields
- `notice_title: str = ""`
- `notice_level: str = "info"`

---

## 五、feishu_client.py（2 项）

### 5.1 SSL certifi 修复
- 导入 `ssl`, `certifi`
- 所有 `aiohttp.ClientSession.request()` 使用 `ssl=ssl.create_default_context(cafile=certifi.where())`
- `upload_image` 和 `_request_json` 中均有 SSL 重试（5 次，间隔递增）

### 5.2 API 方法
- `delete_message()` 方法
- `upload_image()` 方法
- `FormData` import

---

## 六、其他文件（4 项）

### 6.1 runner.py
- `NoopFeishuClient.delete_message()` 兼容方法
- `main()` 中 `os.environ.setdefault("SSL_CERT_FILE", certifi.where())`

### 6.2 process.py
- `PYTHONUNBUFFERED=1` 环境变量传给 sidecar 子进程

### 6.3 config.py
- `DEFAULT_CONFIG["card"]` 中没有 `"timeline_expanded"` 默认值（让 server.py 动态控制）
- 保留 `resend_after_seconds: 60`

### 6.4 metrics.py
- `feishu_delete_attempts/successes/failures`
- `feishu_resend_attempts/successes/failures/fallbacks`

---

## 七、静态资源

- `hermes_feishu_card/assets/loading.gif` — GIF 动画素材

---

## 合并检查清单

| 文件 | 关键标识 | 说明 |
|------|---------|------|
| `render.py` | `loading_gif_img_key` | GIF footer 参数 |
| `render.py` | `show_tool_summary` | 工具摘要配置化 |
| `render.py` | `"生成中..."` | thinking 文案 |
| `render.py` | `delivery_kind == "notice"` | notice 极简卡片 |
| `render.py` | `render_cards(` | 多表格分卡 |
| `render.py` | `_generate_summary_subtitle` | 完成状态 subtitle |
| `render.py` | `_render_thinking_footer_gif` | GIF footer 渲染 |
| `server.py` | `UPLOADED_GIF_IMG_KEYS_KEY` | GIF 上传支持 |
| `server.py` | `_ensure_logger` | 日志初始化 |
| `server.py` | `return None` (thread_id) | 话题禁用 |
| `server.py` | `_render_session_cards` | 多卡片渲染 |
| `server.py` | `_delete_and_resend` | 超时重发 |
| `server.py` | `timeline_expanded=...session.status...` | 动态展开 |
| `hook_runtime.py` | `_event_was_delivered` | 队列抑制修复 |
| `hook_runtime.py` | `return None` (heartbeat/self-improvement) | notice 过滤 |
| `hook_runtime.py` | `gateway shutting` | shutdown notice |
| `session.py` | `model: str = ""` | model 空值 |
| `session.py` | `reply_to_message_id` fallback removed | 回复 ID 修复 |
| `feishu_client.py` | `certifi.where()` | SSL 修复 |
| `feishu_client.py` | `upload_image`, `delete_message` | API 方法 |
| `process.py` | `PYTHONUNBUFFERED` | 实时日志 |
| `config.py` | no `timeline_expanded` default | 动态控制 |
| `metrics.py` | `feishu_delete_*`, `feishu_resend_*` | 指标 |
