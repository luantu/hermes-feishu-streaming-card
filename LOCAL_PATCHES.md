# 本地修订清单

本文档记录本地分支相对于上游（`upstream/main`）的全部修订。
每次合并上游后对比此清单确保不丢失。

> 最后更新：V4.4.6 合并后（2026-09-15，merge commit 58169a2）

---

## 〇-B、V4.4.6 合并冲突保留记录（2026-09-15）

合并基点 `f6be2d1`（v4.4.5）。v4.4.6 吸收了本 fork 〇-A 的 ledgered base 契约
（`0a48d00` harden split ledger compatibility / `ee08f2e` accept Hermes 0.21.1
`_deliver_attachments` record_delivery= kwarg），并为 Hermes 0.21.2+ 引入
`terminal_delivery_state` 生命周期与 `_recover_terminal_card` 终态恢复。冲突 2 处：

### 冲突 1：hook_runtime.py `_exact_base_delivery_hook_available`
- 取上游侧：它覆盖本地 〇-A 的 ledgered 分支，并新增非 decomposed split-ledger
  形态（`send_final_ledgered` + `prepare_exact_base_final_delivery`）。本地无独立行为需要保留。

### 冲突 2：server.py 终态 PATCH 路径
- 两者都保留：本地 `_card_log(PATCH)` 生命周期日志 + 多卡分卡发送（HEAD 侧），
  叠加上游 `terminal_delivery_state = "delivered"` / `_recover_terminal_card`
  恢复路径。顺序：日志 → 上游恢复 → 本地多卡发送。
- 注意：〇-A 的 patcher.py 双形态契约已随 v4.4.5/v4.4.6 进入上游，本地不再有
  patcher 差异；上游 v4.4.6 另引入 `_find_split_decomposed_base_patch_locations`。

### 安装注意（Hermes 0.21.3）
- Hermes 升级会留下陈旧 `.hermes_feishu_card_manifest` 与
  `gateway/run.py.hermes_feishu_card.bak`，v4.4.6 的 ownership 校验会拒绝并报
  `decomposed ownership cannot be verified` / `decomposed backup has no
  manifest`。处理：确认 Hermes 侧 `git status` 干净后删除 manifest 与残留 .bak
  再 `install --accept-hermes-upgrade`（2026-09-15 已执行成功）。
- 0.21.3 上 `base_required: no`、`exact_delivery_contract: not_required`，运行时
  hook 可用性检查通过。

## 〇-A、install 契约适配：Hermes bf53ff0 ledgered base（上游支持已吸收，本地边界仍保留）

Hermes `0.21.1 / bf53ff0`（2026-09-09）把 base.py 的投递账本括号从 `_send_final_text`
重构进新方法 `send_final_ledgered(self, event, session_key, text_content, metadata, *,
reply_to, is_ephemeral_response)`，并在 `_record_delivery_obligation` 中引入
`ledger_message_id` 三语句取 ID 形态。上游 v4.4.5 已加入同一类 split-ledger 支持；本次合并
吸收上游更严格的 decomposed `send_final_ledgered` AST/bracket 校验，同时保留本地旧契约
回退和双形态严格校验，不能因为上游已有同名能力就删除本地边界。

- `install/patcher.py::apply_base_patch` 的选择顺序：
  - v4.4.5 split-ledger + decomposed 形态优先，使用上游严格校验和
    `_render_decomposed_split_base_final_hook_block()`；非 decomposed 的 split 形态使用
    `_render_split_base_final_delivery_hook_block()`。
  - 本地 `_has_decomposed_ledgered_base()` 形态作为兼容回退，使用
    `_render_decomposed_base_final_hook_block_ledgered()`；再回退到上游旧 decomposed
    inline 形态和 legacy inline 形态。
  - `send_final_ledgered` 契约严格校验其签名（kwonly `reply_to` /
    `is_ephemeral_response`）、`_send_final_text` 委托调用、`record_delivery(result)`，以及
    `delivery_adapter` → `_record_delivery_obligation(...)` → `_send_with_retry(...,
    reply_to=reply_to, ...)` → finalize 的顺序；final hook 插入点仍在 ledger bracket 的
    `_send_with_retry` 之前。参数、adapter、终态 guard 或控制流漂移继续 fail-closed。
  - 不存在 `send_final_ledgered` 时保留旧内联括号分支（行为不变）；`record` 方法的
    `compute_obligation_id(...)` 同时接受旧单语句与新的 `_ledger_id` 三语句形态。
- `_find_owned_exact_base_blocks(strict=True)` 同时识别本地旧 ledgered、上游
  split-ledger/decomposed 以及 legacy 模板；apply/remove/restore/doctor 必须逐字可逆，
  不能用宽松 marker 识别替代 AST 契约验证。
- `hook_runtime.py::_exact_base_delivery_hook_available` 的 bracket `co_names` 检查按
  `send_final_ledgered` 是否存在选择对应方法；本地
  `tests/fixtures/hermes_decomposed_ledgered/` 与测试继续覆盖 bf53ff0 旧形态，上游新增
  `tests/fixtures/hermes_split_ledger_base.py` / `test_split_ledger_patcher.py` 覆盖新形态。

> v4.4.5 已提供对应 split-ledger 适配，但本地旧形态 fixture、严格回退和本地 Hermes
> 运行时边界仍是 fork 维护的一部分；下次合并时必须同时检查两套契约及其可逆性。

## 〇-B、V4.4.5 终态稳定性吸收记录（2026-09-14）

- `hook_runtime._event_data()` 传递 Hermes completion 的 `failed` / `interrupted` /
  `partial` / `completed=false` 结果标志。
- `session.CardSession.apply()` 对未成功结果展示失败/中断/不完整提示，不再把带正文的
  非成功结果误报为完成。
- `server._abandon_stale_sessions_for_chat()` 将被新轮次替代的旧卡标为 `failed`，保留
  已有正文并提示“本轮已被新对话替代，任务尚未确认完成”。晚到事件不翻转旧卡，也不污染新轮。


## 〇、V4.4.2~V4.4.4 合并冲突保留记录（2026-09-09）

合并基点为 `aad9c03`（v4.4.1-issue-repairs 分支顶端；上游在 PR #260 合入 main 前
对该分支有过追加提交，导致 merge-base 不在本地历史内——下次合并注意用
`git merge-base` 实际确认，不要假设）。

### 冲突 1：render.py tool_summary / divider 区域（`_render_card_unchecked`）
- 保留本地 1.9：divider 仅在 `footer` 或 `tool_summary_content` 非空时渲染。
- 吸收上游 v4.4.2 的 `session.tool_count` 门控，合并后条件为
  `not timeline_elements and not pending_approval and show_tool_summary and session.tool_count`。

### 冲突 2：render.py `_render_timeline_elements` 空记录分支
- 保留本地行为：初始加载显示「等待工具事件…」占位；非加载且无记录时不渲染折叠条。
- **主动移除**上游新增的 `if not all_entries: return []` 早退——它会杀掉加载占位；
  上游"空 timeline 不渲染"的意图已由本地 `if not entries and not folded` 分支覆盖。

### 冲突 3：tests/unit/test_render.py（4 处）
- 均为"零工具无 timeline"断言，取本地文案断言 + 上游元素 ID 断言的并集。
- 注意：`_timeline_panel` 的 element_id 是 `auxiliary_timeline`，若加载占位渲染，
  上游式 `"auxiliary_timeline" not in str(card)` 断言会失败——相关测试的 session
  均已有 thinking/answer 内容（非 initial loading），并集安全。
- 另按本地行为适配两个上游新测试：
  - `test_render_completed_card_places_attachment_summary_before_tools`：给 session
    加 `model` 使 footer 非空，从而 divider 渲染、排序断言有意义（本地 1.9 divider
    条件渲染，上游是无条件渲染）。
  - `test_render_initial_running_card_shows_context_loading_without_empty_timeline`：
    改为断言本地行为——main content 为"生成中"文字（本地 1.4，非 spinner）、
    保留 `auxiliary_timeline` 加载占位面板（上游 v4.4.2 已删占位，fork 有意保留）。

### 自动合并需复核的上游改动（已确认共存）
- server.py：`interaction.requested` 预检（卡片超限时不 claim 决策，返回
  `interaction_card_limit`）——与本地 emoji 删卡逻辑同函数不同区域，无冲突。
- hook_runtime.py v4.4.4：新增 `_hfc_thread_metadata_for_target_with_feishu_reply_anchor`
  wrapper（重启通知保留在话题内）。**已保留**：它只是透传 Hermes core 已有的
  thread 元数据，不自行创建话题路由；sidecar 侧三锚点（`_thread_id_for_event`
  恒 None、`_reply_to_message_id_for_event` 仅显式 om_、hook_runtime
  `"conversation_id": chat_id` ×3）合并后逐项复核仍为禁用状态。
- hook_runtime.py：adapter 注册表重构（`_hfc_registered_adapter_items`、
  `_adapter_for_source` resolver、`_profile_adapters` 支持）、approval 过期改判 deny。
- render.py：approval/clarify 选项按钮只显示序号 + 正文列选项说明（v4.4.2 交互可读性）。
- cli.py / install：integrity 迁移快照校验、patcher lenient 移除 + `start` 锚点。
- 版本：4.4.1 → 4.4.4（pyproject + `__init__.py`）。

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
- **2026-09-15 重新落实（v4.4.6 合并后）**：上游 0560183 在 `_event_data` 把 Hermes 侧
  `reply_in_thread` 透传进事件数据，v4.4.6 又加 `session.reply_in_thread` 粘性话题
  放置（sticky reply anchor），导致卡片再次变成话题消息。本地修复：
  - `_reply_in_thread_for_event()` 恒 `return None`→恒 `False`（与 `_thread_id_for_event` 同构）；
  - 两处发送点去掉 `or session.reply_in_thread` 粘性消费；
  - sticky reply anchor 门控改为恒空（不因会话粘性带出 `om_` 锚点）。
  - 显式 `om_` `reply_to_message_id` 仍按 2.6 作为普通 reply_to 保留。
  - 已按本地行为适配 6 个上游话题放置测试（重命名 2 个 + 修正断言 4 处）。

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
