# 本地修订清单

本文档记录本地分支相对于上游（`upstream/main`）的全部修订。
每次合并上游后对比此清单确保不丢失。

> 最后更新：V4.3.7 合并后

---

## 一、render.py

### 1.1 GIF 动画 footer
- `render_card()` / `render_card_result()` / `render_cards()` 接受 `loading_gif_img_key: str | None = None`
- `_render_footer()` 接受 `loading_gif_img_key`，非 completed 状态优先用 GIF
- `_render_thinking_footer_gif()`：返回 `custom_icon` markdown 元素
- footer 是 list 时 `elements.extend(footer)` 而非 `append`

### 1.2 tool_summary 配置化
- `DEFAULT_FOOTER_FIELDS` 增加 `"tool_summary"`
- `render_card()` 中 `effective_fields` 计算、`show_tool_summary` 判断
- `_render_footer()` 中 `if field == "tool_summary": continue` 跳过内联

### 1.3 model 空值不显示 + 模型名归一化
- `_render_footer()`：`"Unknown"` → `""`
- `from .model_names import normalize_model_name` 导入（见 6.5）
- `_colored_model_label()` 内部调用 `normalize_model_name()`

### 1.4 thinking 内容用文字
- `primary_text = "生成中..."` 替代 `_spinner_frame()`

### 1.5 notice 卡片极简样式
- `session.delivery_kind == "notice"` 时早期返回极简卡片：无 title/footer/divider，正文 `x-small`，header 只保留颜色条

### 1.6 多表格分卡（`render_cards`）
- `render_cards()` 超过 5 个表格时拆分为多张卡片
- `_split_content_by_tables()` 辅助

### 1.7 完成状态 subtitle 显示正文摘要
- `_render_status()`：completed 时 subtitle 用 `session.answer_text`（不再固定"已完成"）

### 1.8 timeline 动态展开
- `timeline_expanded: bool | None = None`（上游为 `bool = False`）
- 为 None 时 `session.status not in {"completed","failed"}` 动态决定：流式中展开、完成后折叠

### 1.9 空 footer 不显示（含 divider / tool_summary）
- `_render_footer()` 无有效数据（无 model/token/context、duration<=0、无 subscription_usage）时返回 `""`
- `_render_tool_summary()` 无工具时返回 `""`（不再输出"工具调用 0 次"）
- `render_card()` 仅在 footer 或 tool_summary 有内容时才渲染 `main_divider`；footer 空则不渲染 footer 元素
- 已完成回复 footer 不再加 `已完成 · ` 前缀（commit aa74d17）

### 1.10 V4.3.x 交互卡片兼容
- `render_card()` 同时保留本地 `loading_gif_img_key` 与上游 `interaction_profile_id`、`mentions_enabled` 参数
- 主卡保持 `wide_screen_mode: True`
- 上游 `_card_quote_summary()` 摘要逻辑保留
- `normalize_model_name()` 和模型颜色标签逻辑不能被上游交互卡片合并覆盖

---

## 二、server.py

### 2.1 生命周期日志（独立文件）
- `_ensure_lifecycle_logger()`：写到 `~/.hermes/logs/feishu-card.lifecycle.log`（env `HERMES_FEISHU_CARD_LIFECYCLE_LOG` 覆盖）
- `_card_log(level, kind, **fields)`：结构化单行日志，kind ∈ CREATE/RESOLVE/APPLY/BIND/PATCH/TERMINAL/ABANDON/RESET/PROMOTE/DELETE/CONV_FINALIZE/CONV_RELEASE/ORPHAN_FINALIZE/LOCK/ROUTE
- `_content_prefix(session)`：卡片正文前缀（48 字），用于按内容反查日志
- 埋点覆盖：事件入锁、session 解析、apply、建卡/绑定（含 old_card 覆盖检测）、PATCH（含 stale_target 检测）、终态、abandon、interaction 提升、孤儿收尾

### 2.2 孤儿卡超时收尾
- 常量 `CARD_ORPHAN_TIMEOUT_SECONDS`（默认 600s，config `card_orphan_timeout_seconds` 覆盖）
- `_finalize_orphan_sessions()`：周期清理时，把"有绑定卡片 + 仍 thinking + 空闲超时 + 无 pending 交互"的 session 标记 completed 并渲染/PATCH，然后释放
- 接入 `_runtime_cleanup_loop()`（与上游 `_expire_pending_interactions` 并存）

### 2.3 同会话多卡收尾（Hermes 合并轮次兜底）
- 常量 `CONV_FINALIZE_SILENCE_SECONDS = 3.0`
- `_finalize_conv_sibling_sessions()`：终态事件到达后，把同 conversation+chat+profile 仍 thinking 的兄弟卡收尾（渲染 + PATCH），并把终态 footer 元数据应用到这些卡
- `_schedule_conv_sibling_finalize()`：用 `loop.call_later` 延迟调度（不在终态请求路径 sleep）
- 只在 `conv != chat_id`（真实 context，非群聊）时启用，避免群聊终态误伤其他卡

### 2.4 footer 元数据应用到"所有卡"
- `_terminal_metadata_from_event()`：从终态事件提取 model/tokens/context/duration/reply_to_message_id
- `_apply_terminal_metadata_to_session()`：只补 footer 元数据，**不覆盖 answer_text**（避免丢失第一问答案）
- `terminal_already_handled` 分支：对本卡应用元数据 + 传给 conv 收尾应用到兄弟卡

### 2.5 会话释放
- `_release_finalized_session()`：终态 PATCH 完成后立即释放 session（不等 1 小时保留期）

### 2.6 话题/回复路由禁用
- `_thread_id_for_event()` 恒 `return None`（禁 Feishu thread 路由）
- `_reply_to_message_id_for_event()` 只返回显式 `om_` 开头的 `reply_to_message_id`，不自动推导
- V4.3.x 新增 `_reply_in_thread_for_event()` 后仍保持上述本地策略：不根据 `event.message_id` 自动生成 reply anchor；`reply_in_thread` 不得绕过本地 thread 禁用策略

### 2.7 GIF 上传 + 超时重发（遗留）
- `UPLOADED_GIF_IMG_KEYS_KEY`、启动时 GIF 上传
- `RESEND_AFTER_SECONDS_KEY`（`resend_after_seconds`）、`_delete_and_resend()`（注：触发逻辑未接入，为遗留死代码）

### 2.8 emoji-only 应答删卡
- `_is_emoji_only()`：message.completed 的 answer 为纯 emoji 时删除该卡片

### 2.9 sidecar 日志
- `_ensure_logger()`：StreamHandler + INFO

---

## 三、hook_runtime.py

### 3.1 turn_id 懒绑定（无 message.started 的新流）
- `_CANONICAL_TURN_MESSAGE_ATTR`、`_bind_source_turn()`、`_read_source_turn()`
- `_turn_id_for_runtime_event()`：source 无绑定 turn 时，用当前入站 message_id 懒绑定独立 turn_id，避免第二轮被 alias 吸进旧卡覆盖
- source 拒绝绑定（slots）时保持 legacy 无 turn_id

### 3.2 终态/抑制全链路日志
- `_log_terminal_emit()`、`_hfc_policy_terminal_log()`、`_hfc_log_native_send()`（NATIVE_SEND，含调用栈）
- 覆盖：policy pinned/fresh/sync 决策、async/sync/threadsafe emit 入口与 gate=native、terminal emit/result、exact-base stage/staged/applied/PROXY/FALLBACK/SWALLOWED、cron

### 3.3 原生重复发送抑制（修复 `_run_agent_inner` 兜底直发）
- `_HFC_CARDED_CONTENT` 内容注册表（chat_id → 答案签名，TTL 120s）
- `_hfc_record_carded_content()`：exact-base applied 分支 + 普通终态 applied 分支记录卡片化答案
- `_hfc_content_was_carded()`：两侧内容均 ≥60 字且前 60 字相同才判定重复（避免短文本误伤）
- `_hfc_send_with_native_command_result_card()` 兜底放行前查重，命中返回 `_send_result(True, "carded_suppressed")` 吞掉原生

### 3.4 队列完成抑制 + 纯 emoji 应答跳过
- `_event_was_delivered()`：终态事件 `applied=False` 时仍视为已投递
- `_is_emoji_only_answer()`：message.completed 为纯 emoji 时不发射

### 3.5 notice 分类过滤
- heartbeat（`⏳ working`）、self-improvement review 返回 None
- 新增 gateway shutting down / restart 分类（`"网关状态"`）

### 3.6 `should_suppress_native_response` 决策日志
- 拆出 `_should_suppress_native_response()`，外层记录 suppress 决策

### 3.7 V4.3.x native hook bridge 兼容
- 保留上游 `_THIN_INTERACTION_KINDS`、`_THIN_CONTEXT_COMPACTION_MESSAGES`、`HybridTerminalRecord` 等 native hook bridge 结构
- 与本地 `_CANONICAL_TURN_MESSAGE_ATTR`、lazy turn binding、原生重复抑制日志并存

---

## 四、session.py

### 4.1 model 空值
- `model: str = ""`（上游 `"Unknown"`），`session.apply()` 中 model fallback 为 `""`

### 4.2 回复消息 ID 只在显式时赋值
- `message.completed` 处理移除 `elif event.message_id.startswith("om_")` 的 reply_to fallback

### 4.3 notice 字段
- `notice_title` / `notice_level` 保留

---

## 五、feishu_client.py

### 5.1 SSL certifi 修复
- `import ssl, certifi`，`ssl=ssl.create_default_context(cafile=certifi.where())`

### 5.2 API 方法
- `delete_message()`、`upload_image()`、`FormData` import

---

## 六、其他文件

### 6.1 runner.py
- `NoopFeishuClient.delete_message()` 兼容
- `main()` 中 `os.environ.setdefault("SSL_CERT_FILE", certifi.where())`

### 6.2 process.py
- `PYTHONUNBUFFERED=1` 传给 sidecar 子进程

### 6.3 config.py
- `card` 增加 `resend_after_seconds: 60`、`card_orphan_timeout_seconds: 600`
- 无 `timeline_expanded` 默认值（动态控制）

### 6.4 metrics.py
- `feishu_delete_*`、`feishu_resend_*` 指标

### 6.5 model_names.py（新增文件）
- `normalize_model_name()`：剥离 provider 前缀/日期尾号/API 路径、矫正版本号、保留官方子型号
- `_MODEL_FAMILIES`、`_VARIANTS`、`_DISPLAY_NAMES`
- `MODEL_COLOR_PREFIXES` 增加空格后缀匹配 + qwq/qwen/gemini 颜色

---

## 七、静态资源 / 脚本

- `hermes_feishu_card/assets/loading.gif` — GIF 动画素材
- `restart`、`update` — 根目录运维脚本

---

## 合并检查清单（关键标识）

| 文件 | 关键标识 | 说明 |
|------|---------|------|
| `render.py` | `loading_gif_img_key` | GIF footer 参数 |
| `render.py` | `show_tool_summary` | 工具摘要配置化 |
| `render.py` | `_render_thinking_footer_gif` | GIF footer 渲染 |
| `render.py` | `timeline_expanded: bool \| None` | 动态展开 |
| `render.py` | `_render_tool_summary` 返回 `""` | 空 footer/divider 隐藏 |
| `render.py` | `from .model_names import normalize_model_name` | 模型名归一化 |
| `render.py` | `interaction_profile_id` / `mentions_enabled` | V4.3.x @提及交互参数 |
| `server.py` | `_card_log` / `_ensure_lifecycle_logger` | 生命周期日志 |
| `server.py` | `CARD_ORPHAN_TIMEOUT_SECONDS` / `_finalize_orphan_sessions` | 孤儿卡超时收尾 |
| `server.py` | `CONV_FINALIZE_SILENCE_SECONDS` / `_finalize_conv_sibling_sessions` | 同会话多卡收尾 |
| `server.py` | `_apply_terminal_metadata_to_session` | footer 元数据到所有卡（不覆盖正文） |
| `server.py` | `_release_finalized_session` | 终态后释放 session |
| `server.py` | `_thread_id_for_event` 恒 `None` | 话题禁用 |
| `server.py` | `_reply_to_message_id_for_event` 仅显式 `reply_to_message_id` | 禁止自动回复锚点 |
| `server.py` | `_is_emoji_only` | emoji 应答删卡 |
| `hook_runtime.py` | `_bind_source_turn` / lazy-bind | 无 started 新流独立 turn_id |
| `hook_runtime.py` | `_hfc_content_was_carded` | 原生重复抑制 |
| `hook_runtime.py` | `_hfc_log_native_send` / `_hfc_policy_terminal_log` | 终态/抑制日志 |
| `hook_runtime.py` | `_is_emoji_only_answer` / `_event_was_delivered` | 队列抑制 + emoji 跳过 |
| `session.py` | `model: str = ""` | model 空值 |
| `feishu_client.py` | `certifi.where()` / `upload_image` / `delete_message` | SSL + API |
| `config.py` | `card_orphan_timeout_seconds` | 孤儿超时配置 |
| `process.py` | `PYTHONUNBUFFERED` | 实时日志 |
| `metrics.py` | `feishu_delete_*` / `feishu_resend_*` | 指标 |
| `model_names.py` | `normalize_model_name(` | 模型名归一化（新文件） |
| `assets/loading.gif` | — | 静态资源 |
