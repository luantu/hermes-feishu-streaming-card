# 本地修订清单

本文档记录本地分支相对于上游（`upstream/main`）的全部修订。
每次合并上游后对比此清单确保不丢失。

> 最后更新：2026-10-20（〇-E 模型回退通知收卡）；上一位：V5.0.2 合并后
> （2026-10-19，merge commit ed0972b）

---

## 〇-J、V5.0.2 合并记录（2026-10-19，跨大版本 V5）

上游 v4.7.7 → **v5.0.2**（158 提交，247 文件：V5 任务分区阅读/交互续答/维护边界、
localized transient notice recall #434、PM persistent dependencies）。**7 个冲突文件**
（.gitignore/config/feishu_client/patcher/render/server/session，14 块）：

### 结构变化吸收
- **config_rules.py**（V5 新模块）：`config.py` 变为 re-export；本地 fork 定制项
  （`resend_after_seconds`/`card_orphan_timeout_seconds`）移入 config_rules 的
  DEFAULT_CONFIG；`timeline_expanded` 默认值继续不设（LOCAL_PATCHES 6.3）。
- **install/base_contracts.py**（V5）：本地 `_find_decomposed_base_patch_locations`
  等被上游吸收后删除（patcher 改从 base_contracts import）；本地 ledgered renderer
  保留作旧形态兼容。
- **event_rules.py**（V5）：`thread_id_for_event`/`reply_to_message_id_for_event`/
  `reply_in_thread_for_event` **三个 fork 策略函数统一改在本模块**（恒 None / 仅显式
  om_ / 恒 False）——一处改全链路（server 的 placement 与全部 7 处调用点自动生效）。
- **server.py 的 placement 体系**（V5）：`interaction_reply_placement` 采用上游，
  `session_reply_in_thread=False` 禁用 sticky（fork 2.6）；`deliver_terminal`
  （V5 终态投递：PATCH→retry→recover once）取代本地 `_retry_terminal_update`/
  `_recover_terminal_card`；本地 stale_target 埋点、PATCH 埋点、多表格分卡
  （`_render_session_cards`）保留。
- **render.py**：compact/task footer 的模型名改用 `_colored_model_label`（归一带色，
  fork 6.5 在 task 模式同样生效）。

### ⚠️ PM 双源冲突（本次安装最大的坑，运维记录）
安装时报 `PM admission refused`：**两个声明插件同时 enabled**——
`hermes-feishu-card-runtime`（2026-10-09 Codex 建的，uv source 指向**仓库目录**）
与 `hfc-runtime-dependency`（V5 新机制，**wheel 路径源**）——PM 解析同一包双源冲突。
**处理**：从 `/Volumes/ExtWorkspace/.hermes/config.yaml` 的 `plugins.enabled` 移除
`hermes-feishu-card-runtime`（备份 `config.yaml.bak-before-v5-install`），重跑 install
后 PM 重建环境（bdbb9d70）成功注册 5.0.2。**恢复 install 前的兼容改动**：PM 环境需
`ruamel.yaml`（Hermes PM resolver 依赖），以及本机需真实路径 HERMES_HOME：
`HERMES_HOME=/Volumes/ExtWorkspace/.hermes python3 -m hermes_feishu_card.cli install
--hermes-dir /Volumes/ExtWorkspace/.hermes/hermes-agent --yes`（V5 的 `_safe_directory`
拒绝符号链接祖先，`/Users/luantu/.hermes` 链接路径会报 "PM dependency directory
ancestry must be real directories"）。

### 结果
全量 60 failed / 6657 passed vs 基线 91 failed / 5033 passed（**零新增失败、净修复
31 个**）；fork 特性锚点 18/18 在位。测试需 `HFC_FIXED_TAG_SOURCE_ROOT` 指向
v2026.8.3 的 Git checkout（**必须用 /private/tmp 真实路径，/tmp 符号链接会被
native probe 拒绝**）。

---

## 〇-I、V4.7.4 合并记录（2026-10-10）

---

## 〇-I、V4.7.4 合并记录（2026-10-10）

上游 9 提交（managed runtime sidecar recovery，PR #381）：**独立侧车环境**
（新增可选 `service.python_executable`——sidecar 可指向预先装好同版本 HFC 的独立
Python 环境，**官方化本 fork 手动 `uv pip install --reinstall` 的解耦方案**；不存在的
环境/版本不符/editable 安装会被拒绝）、**Gateway/Desktop 进程身份区分**（维护操作只
接受经验证 Gateway 身份）、**退出回收**（PID 存活/出生标识核对，防 PID 复用）。

**零冲突合并**；89 failed / 4868 passed vs 基线 89 failed / 4829 passed（零新增失败、
修复 1 个基线失败）；全部锚点在位（thread 禁用、GIF 分支、模型归一化、生命周期日志、
通知双语分类与转卡日志、notice_producers 双语）。
**PM 环境已同步 4.7.4**（uv pip install --reinstall，见 〇-H 流程）。
`service.python_executable` 可作为后续把 sidecar 从 Hermes PM 环境解耦的可选项，
本 fork 暂未启用（当前手动同步 PM 已稳定）。

---

## 〇-H、⚠️ 关键运维知识：gateway 从 PM 环境的 site-packages 加载 HFC（2026-10-10）

**最终验证（2026-10-10 16:1x）：default 与 coach 的通知均已恢复无头极简卡（用户确认）。
生效顺序 = ①仓库修复 → ②PM 环境 `uv pip install --reinstall` 同步 → ③重启 sidecar + gateway。**
（coach 的残留失败——230002 / 可能的 ReplyThreadAnchorMissing——在最后一轮 sidecar 重启后消失；
两个 `not_sent` 分支与 FeishuAPIError 分支现均有含 bot/chat hash 与 error_kind 的诊断日志。）

**sidecar 日志真实路径是本机 `~/Library/Logs/Hermes/feishu-card.stderr.log`**（launchd
StandardErrorPath 重定向），不是外置卷 `~/.hermes/logs/`（那是迁移前的旧文件，早停更）。

**Externally-supervised gateway（`ai.hermes.external.gateway`，2026-10-09 Codex 会话部署）
不再从仓库加载 `hermes_feishu_card`，而是从 Hermes PM 环境的 site-packages 副本加载：**

```
/Volumes/ExtWorkspace/.hermes/installs/<install-hash>/environments/<env-hash>/venv/lib/python3.14/site-packages/hermes_feishu_card/
```

该副本由声明插件 `/Volumes/ExtWorkspace/.hermes/plugins/hermes-feishu-card-runtime`
（pyproject 的 uv path source 指向本仓库）在**安装/重建环境时**构建。
**仓库更新后副本不会自动同步**——本次通知修复因此长时间"不生效"（gateway 一直跑
10-09 的旧副本）。sidecar（`hermes-agent/venv/bin/python -m hermes_feishu_card.runner`）
仍从**仓库源码**加载，两个进程会跑不同版本！

**每次修改 hook_runtime/notice_producers 等 gateway 侧代码（或合并上游）后必须同步：**

```bash
# 找到当前环境（gateway 报错 traceback 里的 site-packages 路径，或最新 mtime）
PM_ENV=/Volumes/ExtWorkspace/.hermes/installs/2fa32c94405f8f7e/environments/<env-hash>/venv
uv pip install --python $PM_ENV/bin/python --reinstall --no-deps /Volumes/ExtWorkspace/.hermes/feishu-card
# 然后重启 gateway
hermes gateway restart   # 或 launchctl kickstart -k gui/$(id -u)/ai.hermes.external.gateway
```

**验证同步生效**（应出现取证日志）：
```bash
grep "command card adapter methods installed" ~/Library/Logs/Hermes/gateway.error.log
```

**注意**：
- PM 环境无 pip，用 `uv pip install --python <venv>/bin/python`。
- Hermes 重建环境时会从声明插件重新解析 path source → 自动拿到最新仓库代码（自愈）。
- gateway 的启动/关闭通知读 `.restart_pending.json` marker 的 delivered_targets，
  会**跳过**已通知过的飞书 chat（测试通知时先 `rm -f ~/.hermes/.restart_pending.json`）。
- 通知的网关状态日志：`producer notice card delivered` / `classified notice card delivered`
  / `...failed; falling back to native text`（gateway.error.log）。

---

## 〇-G、网关通知卡片修复：Hermes zh i18n + 直连 send（2026-10-10）

**现象**：重启/上线等通知不再转 notice 无头极简卡，以原生大消息发出。

**根因（三层）**：
1. **i18n**：Hermes v0.21.6 把网关通知本地化（"⚠️ Hermes 正在重启——…"、
   "♻️ 网关已上线——Hermes 已恢复就绪。"），HFC 分类表只匹配英文关键字 → 失配。
2. **直连 send**：v0.21.6 的 `_send_shutdown_notice`/`_send_restart_notification`/
   `_send_home_channel_message` 直接走 `adapter.send`，**不再经过**
   `_deliver_platform_notice`（HFC 唯一的转卡拦截点）→ sidecar 全程未捕获。
3. **PM 副本**（见 〇-H）：上述修复在仓库里就位后，gateway 仍跑 PM 旧副本 →
   需 `uv pip install --reinstall` 同步 + 重启（**这才是最终生效的一步**）。

**修复**（`hook_runtime.py` + `notice_producers.py`）：
- 分类表加中文变体（restart/shutdown/online；`hermes is restarting/shutting down`
  英文正式文案也补上）；`gateway-shutdown`/`gateway-online` 路由走独立极简卡
  （与 heartbeat/background-task 同列）。
- 重启完成（restarted）保持纯文本契约（用户此前要求），plain_text 按通知自身
  语言输出（中文通知不再被替换成英文常量）。
- `notice_producers` 双语常量集合（ONLINE_TEXTS / SHUTDOWN_NOTICE_TEXTS /
  RESTARTED_TEXTS），recall 身份识别在中英两种文案下都成立。
- **send 包装层转卡**（`_hfc_send_with_native_command_result_card`）：识别到的
  已登记 producer 通知改为经 `_hfc_send_system_notice_card(force_independent=True)`
  发卡；卡片发不出（无卡模式/分类未命中/sidecar 不可用）时回退原生文本，
  保证通知不丢；recall 登记在两条路径都保留。

**回归边界**：notice 测试集合改动前后一致（5 个既有失败无新增）；
新增 3 个单测覆盖中文分类、restarted 双语言 plain_text、独立 scope 路由。

---

## 〇-F、V4.6.13~V4.7.3 合并冲突保留记录（2026-10-09）

上游 44 提交（v4.6.13 → v4.7.3：task 阅读预设、审批回执架构重构、心跳完整性降频、
Python 3.14 兼容、slash callback 修复）。冲突 3 文件：

### AGENTS.md
采用上游 v4.7 重写结构（Delivery and release 段），保留 fork 特有段
（fork-maintenance-guide 指引、wiki 页列表、Obsidian LLM Wiki 段、stability 段）；
旧内联测试矩阵/Release Checklist 被上游 wiki 引用取代。

### render.py（3 块）
- timeline 动态展开（1.8）与上游 task 预设 `TASK_TEXT_SIZE_DEFAULTS` 并存。
- `_render_footer` 调用/签名：本地 `loading_gif_img_key` 与上游
  `compact`/`include_status`（task 模式）并存。

### server.py（2 块）+ 两个架构适配（重要）
1. **渲染选项改用上游 `**card_render_options(card_config)` 抽象**（v4.7 新的
   render_options.py，含 presentation/width_mode/table_overflow 归一化），
   本地 `loading_gif_img_key` 保留；`timeline_expanded` 以 dict 内合并方式覆盖
   `card_render_options` 的静态默认（`**{**options, "timeline_expanded": ...}`——
   不能写成尾随 kwarg，会与展开的同名键冲突报
   `got multiple values for keyword argument`）。
2. **退役交互卡 owner 提升**：本地旧行为把 interaction 卡 promote 为 session owner
   （feishu_message_ids 指向交互卡、原卡显示"已转入交互卡片"）。上游 v4.7 把交互卡
   独立为 legacy 回执卡、原流式卡保持 owner 并内联显示选择 scope——整个
   receipt/continuation 管线（approval_retirements、legacy_owner_receipt、
   display_segments）依赖该拆分，故提升逻辑退役（PROMOTE 日志保留）。
3. **`_retire_continuation_predecessor` 加方言守卫**：前驱是交互卡本身
   （`interaction.feishu_message_id == message_id`）时跳过 2.0 PATCH，
   防止以 schema-2 破坏 legacy 回执卡。

### 结果
全量 89 failed / 4826 passed vs 基线 125 failed / 4239 passed：**零新增失败，
且净改善 36 个**——〇-C 节记录的 v4.6.4 时代待甄别项（approval_terminal_cleanup、
interaction_continuation 等）随上游架构重构全部通过，待甄别清单清零。

---

## 〇-E、V4.6.12 合并记录（2026-09-30）

### uniapi 模型名归一化修复（6.5 增强，commit 5efcaa1）
uniapi.ruijie.com.cn 两个 provider（uniapi-high / custom）的模型 ID 形如
`qwen3.8-flash`（家族+版本粘连、带或不带 `uniapi/` / `zj-` / `ali-` 前缀），旧逻辑
把家族当 provider 剥掉，footer 只显示变体（"Flash"）且因无法匹配颜色前缀显示灰色。
修复：
- `_strip_provider_prefix` 新增 `_STUCK_FAMILY` 粘连拆分（`qwen3.8` → `qwen-3.8`），
  斜杠后 chunk 同样处理（`uniapi/qwen3.8-flash`）。
- `_DECIMAL_VERSION` 收紧为 `(\d)-(\d+)(?![\w.])`：`claude-haiku-4-5` 仍折叠为 4.5，
  但 `qwen-2.5-72b` 的尾段不再被融合成 `2.5.72b`。
- `MODEL_COLOR_PREFIXES`：Qwen 从 grey（未识别兜底色）改为 carmine，QWQ 改为 yellow。
- uniapi 全部 7 个模型 ID（ali/zj 前缀、glm-5.3-flash、gpt-5.6-luna、qwen3.8-flash）
  双形态（裸 ID + `uniapi/` 前缀）验证显示与配色正确；测试用例补入
  `test_model_footer_keeps_family_after_provider_prefix`。

---

## 〇-E、V4.6.12 合并记录（2026-09-30）

合并基点 `9b45913`（v4.6.11 上游点），上游 6 提交（可配置 JSON 2.0 卡片宽度
`card.width_mode` + 当前 Hermes reply-clock 契约 + thinking-tail 测试稳定化）。
唯一冲突：render.py imports——本地 `model_names.normalize_model_name` 与上游
`config.card_width_config` 并存（都保留）。全量测试 **0 新增失败**（124 failed 与
基线完全一致，上游新增 65 个测试全过）；本地文件与全部锚点合并后逐项验证在位。

---

## 〇-D、V4.6.5~V4.6.11 合并冲突保留记录（2026-09-29）

合并基点 `457f0d0`（v4.6.4 上游点），上游 32 提交（v4.6.5 → v4.6.11：群聊并发隔离、
live thinking overflow 修复、compact choice rows、notice producer 拆分、后台进程上下文、
`thinking_body_tail_chars` / `timeline_order` / `timeline_tools_per_reasoning` 新配置）。
冲突 5 文件：

### config.py（本地 6.3 特性）
- 保留本地"无 `timeline_expanded` 默认值"（动态解析），吸收上游
  `timeline_order: "newest_first"`、`timeline_tools_per_reasoning: 0` 两个新默认键。
- tests/unit/test_config.py 两处期望字典同步处理。

### hook_runtime.py emit applied 判定
- 本地 `_event_was_delivered`（suppress 友好语义，3.4）保留为默认路径；
  上游新增 `require_ack=True`（system.notice 场景）时走 `_event_was_applied(strict=True)`。
- 本地 terminal emit result 日志（3.2）保留。

### render.py（2 块）
- imports：本地 `model_names.normalize_model_name` 与上游
  `approval_receipts.has_confirmed_approval_receipt` 并存。
- timeline 选择：吸收上游 running-tool 优先 / `_limit_tools_per_reasoning` /
  `priority_tool_ids` 逻辑；**继续移除上游 `if not all_entries: return []` 早退**
  （会杀掉本地"等待工具事件…"加载占位；空记录分支由本地逻辑处理）。

### server.py（本地 1.8/2.6 特性）
- `timeline_expanded` 保持 `_resolve_timeline_expanded(card_config)` 动态解析
  （上游改回 `_safe_bool(..., False)`，fork 不采纳）；吸收上游
  `timeline_order` / `timeline_tools_per_reasoning` / `thinking_body_tail_chars` 传递。

### 本地特性退役记录：重复终态重发卡（原 2.4 兜底）
本地旧特性"已终态 session 收到重复 terminal 事件时重渲染/PATCH 卡片"已在本次合并
**主动退役**：上游 v4.6.9 的终态幂等保护是群聊并发隔离（#348，15 个测试）的前提，
且上游已有有界终态重试（`terminal_delivery_retry`）。合并后重复/晚到 terminal 事件只记
`_card_log`（TERMINAL already_handled，本地日志保留）并返回 `applied=true`
（仍抑制网关原生重发），不再触碰已完成的卡。
`test_group_concurrent_requesters_keep_own_final_cards` 18 个实例全部通过。

### 本地文件存活验证（合并后）
`model_names.py`、`assets/loading.gif`、`LOCAL_PATCHES.md`、`restart`、`back-restart`、
`docs/fork-maintenance-guide.md`、`update` 全部在位；全部锚点 grep 通过（含 GIF 全程
footer 分支、话题禁用三锚点、生命周期日志、emoji 删卡、懒绑定、原生抑制、ledgered 契约）。

### 已知待甄别项（上游 v4.6.5+ 新功能场景，非本地回归）
合并后全量 124 failed / 4168 passed / 28 skipped vs 基线 117 failed / 3950 passed /
18 skipped；其余失败均在基线集合内。新增 12 个失败集中在两个上游 v4.6.5+ 新功能
文件（合并前不存在）：
- `test_approval_terminal_cleanup.py`（4 测试 10 实例）：approval_receipts 回执与
  display continuation 的交互——mock 的 `update_card_message` schema 一致性断言失败
  （interaction 阶段后对 card-1 的 PATCH schema 与卡不匹配，卡停留在初始内容）。
- `test_interaction_continuation.py::test_confirmed_handoff_freezes_old_card_without_claiming_turn_success`
  （2 实例）：同类的 confirmed-handoff 场景。

调查线索：`_update_card_for_app` 抛 AssertionError（mock schema 断言），疑与
`_existing_owner_render_result` / continuation 打开后的 owner 渲染方言判定和本地
2.3/2.5 收尾逻辑的交互有关。不影响安装与既有功能路径（patcher 与既有功能测试全过）。
下次合并前应逐项确认。

---

## 〇-C、V4.5.0~V4.6.4 合并冲突保留记录（2026-09-20）

合并基点 = 本地 HEAD d1aab00（含并发会话的 v4.4.6 合并 + 压缩通知独立卡等本地提交）。
上游跨度 v4.5.0 → v4.6.4（84 提交，141 文件，+13956/-4251）。冲突 6 文件：

### 冲突 1：render.py（7 块）
- imports：保留本地 `from .model_names import normalize_model_name`，并吸收上游
  `card_timeline.TERMINAL_TOOL_STATUSES`、`session.ToolState/_runtime_tool_summary`。
- notice 极简卡片早期返回（本地 1.5）保留；`_primary_text_for_session` 吸收上游
  `stream_thinking_to_body` 参数。
- footer 调用保留本地 `loading_gif_img_key`（1.1）。
- tool_summary/divider 区域（本地 1.9）：divider 仍条件渲染（footer/tool_summary 有内容
  才渲染），吸收上游 `hide_terminal_tools`/`tool_activity_elements` 门控。
- completed subtitle（本地 1.7）：保留正文摘要（上游 v4.6 改回固定"本轮回复结束"，
  fork 不采纳）。
- timeline：保留本地"加载占位 + 无记录隐藏折叠条"，**移除上游 `if not all_entries:
  return []` 早退**（会杀掉加载占位），吸收上游 `live_thinking` 实时思考入口。
- footer 状态文本（等待/running）：采用上游 v4.6 增强版（工具数/耗时/动作短语/live
  clock），保留本地 GIF：纯初始加载（无工具、无动作短语）时仍优先 GIF 动画。
- 上游 v4.6 header 状态前缀（`⏳ 执行中 · Hermes Agent`）为上游新契约，吸收。

### 冲突 2：server.py（2 块）
- imports：本地 `render_card` 与上游 `_primary_text_for_session`/`_render_limit_handoff_card`
  并存（都保留）。
- PATCH 日志（本地 2.1 `_card_log`）与上游 heartbeat recall 调度并存。

### 冲突 3：hook_runtime.py（7 块）
- sync/threadsafe emit：本地终态进入日志 + 上游 `_hfc_eager_ensure_command_card_hooks`
  并存。
- async emit：本地 answer.delta 累积/emoji-only 跳过 + 上游终端有界重试
  （`_post_terminal_with_retry`）并存。
- notice anchored_scope：本地 `force_independent` 门 + 上游 heartbeat 独立 scope
  （含 `_hfc_independent_notice_message_id` anchor 重绑定）。
- 原生发送抑制（本地 3.3 `_hfc_content_was_carded` + card-enabled full answer）保留，
  吸收上游 `_hfc_recall_plain_text_status_notice` 撤回。
- platform notice：上游 private delivery 检查 + 本地 force_independent 剥离 thread_id
  并存。
- 本地 `_bind_source_turn`/`_read_source_turn`（懒绑定 3.1）与上游 `bind_agent_reasoning`
  并存。

### 冲突 4：runner.py
- 本地 SSL certifi 设置（6.1）+ 上游 `_configure_logging()` 并存。

### 冲突 5/6：tests/unit/test_render.py、test_e2e_preview.py
- 按本地行为修正断言：初始卡 title 吸收上游 `⏳ 执行中 ·` 前缀（main 仍断言"生成中"
  文字，本地 1.4）；failed 无数据卡 footer 不渲染（本地 1.9，删上游"已停止" pill 断言）；
  model 归一化显示大写（`GPT 5.5`）；completed 无数据卡 footer 不存在。
- notice 测试：`payload["conversation_id"]` 断言改为 `oc_topic`（本地强制 chat_id，
  话题禁用策略 2.6；thread_id 透传但 sidecar 端 `_thread_id_for_event` 恒 None 兜底）。

### 上游删除文件的本地恢复（重要）
- **`hermes_feishu_card/model_names.py`**：上游 v4.6 删除（合并自动删除），本地 render.py
  仍引用 `normalize_model_name` → 从合并前 HEAD 恢复文件。
- **`hermes_feishu_card/assets/loading.gif`**：上游删除，本地 GIF footer 特性依赖 →
  从合并前 HEAD 恢复。
- 并发会话 stash 改动（uniapi/ 等 provider 前缀归一化修复 + 测试）已随合并恢复并应用。

### 合并中修复的一个真实 bug
- `emit_from_hermes_locals_async` 本地日志直接访问 `order_identity.turn_id/turn_key`
  属性，而上游测试用字符串 stub → AttributeError 被 `except Exception` 吞掉导致终态
  投递静默失败。已改为 `getattr` 安全访问（真实环境行为不变），
  `test_terminal_events_take_the_retrying_path` 通过。

### 已知待甄别项（上游 v4.6 新功能场景，非本地回归）
合并后完整测试 127 failed / 3940 passed / 18 skipped vs 基线 113 failed /
3495 passed / 9 skipped。全部失败均在基线集合内，**另新增 6 个 integration 失败**
（均为上游 v4.6 新功能测试，合并前不存在）：
- `test_combined_stability.py::test_restart_does_not_refill_original_after_terminal_recovery_send`
- `test_interaction_continuation.py::test_continuation_send_failure_keeps_original_content_and_does_not_retry_each_delta`
- `test_legacy_owner_fallback.py::test_restored_legacy_owner_does_not_change_new_text_receipt_dialect[completed/failed]`
- `test_server_notice_lifecycle.py::test_completion_notification_waits_for_success_and_keeps_the_receipt`
- `test_server_notice_lifecycle.py::test_hook_registration_and_event_delivery_share_the_single_client_profile`

特征：续答分段失败重试、跨进程 session_store 恢复、notice 生命周期收据——与本地
2.3 同会话多卡收尾 / 2.5 会话释放 / 3.5 notice 分类过滤的交互有待甄别。不影响
安装/现有路径（patcher 与既有功能测试全过）。下次合并前应逐项确认。



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

## 〇-C、hygiene 压缩通知收纳进 notice 极简卡（2026-09-15，本地新增补丁组）

Hermes 的会话卫生压缩通知（如 zh `gateway.compress.turnhold_deferred`
"ℹ️ 上下文压缩已推迟 — 摘要仍在生成中。本回合将不压缩继续。"）由
`run_turn.py::_hmwa_hygiene_notify` 经适配器裸 `send()` 原生直发，绕开卡片链路，
飞书原生文本样式过大。本地新增补丁组收纳进 notice 极简卡：

- `install/patcher.py`：新增 `HYGIENE_NOTICE_PATCH_BEGIN/END` marker、
  `_render_hygiene_notice_hook_block`、`_apply_hygiene_notice_patch`（锚定
  `_hmwa_hygiene_notify` 函数体开头插入 hook，函数缺失则 no-op），接入
  `apply_gateway_fragment`、`remove_patch`、`remove_patch_lenient` 元组与
  run.py `LegacyTargetPatchAdapter.owned_markers`。
  hook 块复用 `handle_platform_notice_from_hermes(self, source, message)`，
  命中分类即 `return None` 抑制原生直发；未命中/异常 fail-open 回原生。
- `hook_runtime.py::_hfc_classify_system_notice`：新增中文压缩通知匹配
  （`上下文压缩` / `压缩已中止` / `压缩模型` → `compression` 分类）；英文
  变体已被既有 `"context compression"` 规则覆盖。notice 卡经
  `_hfc_schedule_platform_notice_card` 投递（metadata=None，不进话题，符合 2.6）。
- **2026-09-17 补充：强制独立极简卡。** 首版命中后因 source 携带 message_id
  上下文，notice 被 `_hfc_send_system_notice_card` 锚定为 session 范围、只成为
  当前流式卡 timeline 的辅助条目（完成后折叠不可见，用户感知为"消息消失"）。
  现为三层链路（`_hfc_send_system_notice_card` / `_hfc_schedule_platform_notice_card` /
  `handle_platform_notice_from_hermes`）增加 `force_independent` 开关，hygiene
  hook 块固定传 `force_independent=True`，压缩通知始终以独立 notice 极简卡
  投递（`notice_scope="independent"`，独立 message_id，按内容+锚点去重）。
  **补充（同日）**：force_independent 时 reply_to 置 None 并剥离 context 的
  thread_id——通知卡不引用触发消息、不进话题（原生行为是独立一条消息，
  引用会让它在会话里看起来像回复某条消息）。
- 测试：`test_apply_patch_installs_hygiene_notice_card_hook`、
  `test_chinese_compression_notice_classification`、ledgered 往返断言；
  两个 fixture 的 `run_turn.py` 增加 `_hmwa_hygiene_notify` 方法。

> 上游若自行实现同类通知卡片化，合并时以上游为准并移除本节差异。

---

## 〇-D、后台审查（自我改进）通知收纳 + 裸发通道审计（2026-10-13，本地新增补丁组）

后台审查摘要（"💾 自我改进回顾：技能 'x' 已修补 · … · Background review may not
delete memory entries…"）由 `agent/background_review.py` → gateway
`run_turn_runner.py::_make_bg_review_callbacks` 的 `deliver()` 闭包 →
`_send_status_text` → 适配器裸 `send()` 原生直发，绕开全部 HFC 钩子（第三条
裸发通道），且 v4.7.7 分类器已无 self-improvement 规则。本地新增：

- `install/patcher.py`：`BG_REVIEW_NOTICE_PATCH_BEGIN/END` +
  `_render_bg_review_notice_hook_block` + `_apply_bg_review_notice_patch`
  （锚定 `_make_bg_review_callbacks` 内嵌套的 `def deliver` 闭包体顶部——
  同步方法，新增 `_find_function_def` 查找器；factory 在而 deliver 缺失时
  **抛错拒装**，契约漂移必须可见）。接入 `apply_gateway_fragment`、
  `remove_patch`、lenient 元组、run.py adapter owned_markers。
  hook 复用 `handle_platform_notice_from_hermes(self._runner, ctx.source,
  message, force_independent=True)`，独立极简卡、无引用、不进话题（〇-C 语义）。
- `hook_runtime.py::_hfc_classify_system_notice`：新增
  `自我改进回顾` / `self-improvement review` / `background review` →
  `self-improvement` 分类（zh+en）。
- 测试：`test_apply_gateway_fragment_installs_bg_review_notice_hook`、
  `test_self_improvement_review_notice_classification`、decomposed 断言；
  两个 fixture 的 `run_turn_runner.py` 增加 `_make_bg_review_callbacks`。

### 裸发通道审计（gateway 直接 `adapter.send` 的其余用户可见通知）

| 通道 | 位置 | 处置 |
| --- | --- | --- |
| 卫生压缩通知 | `run_turn.py::_hmwa_hygiene_notify` | 〇-C 已钩（独立极简卡） |
| 后台审查摘要 | `run_turn_runner.py::_make_bg_review_callbacks` | 本节已钩 |
| platform notice | `run_notifications.py::_deliver_platform_notice` | 上游锚点已钩 |
| 状态回调管线 | `_status_callback_sync` → `_send_or_update_status_coro` | status 锚点已钩（裸发仅为 hook 拒绝后的 fallback） |
| 网关关闭/重启通知 | `run_shutdown.py::_send_notice_logged` | **候选**：走原生；已有"网关状态"分类语义，如需收卡再扩 |
| 会话停滞提醒 | `run_watchers.py`（stall notification） | **候选**：走原生 |
| 看板订阅推送 | `kanban_watchers_notifier.py` | **候选**：走原生 |
| /goal 状态行 | `run_goals.py::_send_goal_status_notice` | 低优先（偏会话性） |
| 斜杠命令 ack | `run_busy.py::_send_command_ack` | 保持原生（会话性反馈） |
| 未授权 DM 拒绝 / 语音转写回显 | `run_inbound.py` | 保持原生（会话性/安全反馈） |

> 后三个候选（shutdown / stall / kanban）要收卡时按本节同一模式扩展：
> 钩子 + 分类器规则 + force_independent 独立极简卡。

---

## 〇-E、模型回退通知收纳进 notice 极简卡（2026-10-20，本地新增补丁组）

Hermes 的模型回退通知（"⚠️ Model fallback: tx-deepseek-v4-1-flash via custom
unavailable (rate limit); using glm-5.3-flash via custom. Primary retry eligible
in ~60 s; recovery is not guaranteed."）走**状态回调管线**而非通知生产者：
`agent/chat_completion_helpers.py::_buffer_fallback_notice` →
`_emit_pending_fallback_notice`（agent/status_output.py，经
`_emit_diagnostic_status`）→ gateway `run_turn_runner.py::_status_callback_sync`
（HFC status 锚点未识别该文案，返回 False）→ `_send_or_update_status_coro` →
`adapter.send`（飞书适配器无 `send_or_update_status`）。

分类器此前没有该文案的规则，`_hfc_send_system_notice_card` 返回
"not a system notice"，落回原生大文本（用户报"为什么没有被 notice 消息收编"）。

- `hook_runtime.py::_hfc_classify_system_notice`：新增 `_MODEL_FALLBACK_NOTICE_RE`
  （`\A⚠️?\s*(?:Model fallback|模型回退)\s*[:：]`，行首锚定——正文中引用该短语的
  回答不误判）→ `model-fallback` 分类（title 模型回退 / level warning /
  `notice_terminal: True`）。命中后由 send wrapper 的既有分类投递路径成卡，
  原生文本不再重复发出。
- `_hfc_send_system_notice_card`：`model-fallback` 加入
  `{"background-task", "gateway-shutdown", "gateway-online"}` 独立作用域集合
  （切换模型是独立一条消息，不折进当前回合卡）。
- 测试：`test_model_fallback_notice_classifies_as_its_own_warning_notice`、
  `test_quoted_or_loose_fallback_wording_is_not_a_notice`、
  `test_status_rail_model_fallback_send_becomes_an_independent_notice_card`、
  `test_model_fallback_notice_degrades_to_native_text_when_the_sidecar_is_off`
  （sidecar 关闭时回落原生原文，绝不静默丢失通知）。

> 上游若自行实现同类通知卡片化，合并时以上游为准并移除本节差异。

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
| `hook_runtime.py` | `_MODEL_FALLBACK_NOTICE_RE` / `"model-fallback"` | 模型回退通知收卡（〇-E） |
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
