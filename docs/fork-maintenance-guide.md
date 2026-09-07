# Fork 维护指南：上游更新纪律 + 安装方法

本文档面向本 fork（`luantu/hermes-feishu-streaming-card`）的日常维护，记录从上游
（`baileyh8/hermes-feishu-streaming-card`）拉取更新的纪律、本地修订的保留策略，
以及将插件安装回 Hermes 的完整方法、注意事项与常见故障排查。

所有命令在本仓库根目录执行，Hermes 安装目录以 `~/.hermes/hermes-agent` 为例。

---

## 一、仓库结构速览

| 项目 | 值 |
|------|-----|
| fork 远端 | `origin` = `https://github.com/luantu/hermes-feishu-streaming-card.git` |
| 上游远端 | `upstream` = `https://github.com/baileyh8/hermes-feishu-streaming-card.git` |
| 本地修订清单 | `LOCAL_PATCHES.md`（每次合并后必须逐项核对） |
| 主分支 | `main` |
| Hermes 安装目录 | `~/.hermes/hermes-agent` |
| Sidecar 配置 | `~/.hermes/feishu-card/config.yaml` |

> **黄金规则：** 合并上游前，先读 `LOCAL_PATCHES.md`。它是本地修订的唯一真值源，
> 合并后必须逐条确认未丢失。

---

## 二、从上游更新的纪律

### 2.1 检查上游更新

```bash
git fetch upstream
git rev-list --left-right --count upstream/main...main   # 左=落后数 右=领先数
git log main..upstream/main --oneline                    # 上游新增提交
git tag --sort=-v:refname | head -5                      # 上游最新版本
```

### 2.2 合并前的准备

1. **确认工作树干净**：`git status --short`。有未提交改动时先决定提交或 stash。
   - 本仓库常出现另一个 Agent（Codex 会话）的并发未提交改动。合并前必须先处理，
     避免 merge 报 `Your local changes ... would be overwritten`。
2. **通读 LOCAL_PATCHES.md**，记住所有本地修订的位置与关键标识。
3. **判断上游版本跨度**。跨度大（如 v4.2.9 → v4.3.7 跨多个大版本）时，冲突会更多，
   需要逐个冲突块决策，不能图省事全取上游。

### 2.3 执行合并

```bash
git merge upstream/main --no-edit
```

自动合并失败时：

```bash
git diff --name-only --diff-filter=U    # 列出冲突文件
```

### 2.4 冲突处理原则

每个冲突块都要判断：**本地修订要保留吗？上游新功能要保留吗？**

| 冲突类型 | 处理 |
|---------|------|
| 本地修订 vs 上游无关新增 | 两者都保留（各自独立代码段） |
| 本地修订 vs 上游重写同一逻辑 | 逐行合并，保留本地行为 + 吸收上游有价值部分 |
| 上游新增参数/字段 | 补进本地调用点，不改本地默认行为 |
| 纯测试断言冲突 | 按实际行为修正断言 |

**本 fork 必须保留的本地修订**（详见 `LOCAL_PATCHES.md`）：

- **引用回复不进入话题群**：`server.py::_thread_id_for_event()` 恒 `return None`；
  `_reply_to_message_id_for_event()` 只返回显式 `om_` 开头的 `reply_to_message_id`；
  `hook_runtime.py` 中 `"conversation_id": chat_id`（3 处）。
  - ⚠️ 上游多次尝试恢复 topic 支持（如 v4.4.1 的 `bind_agent_turn_identity`/
    `redirect_turn_id_for_agent`），合并后必须验证这三个锚点仍是禁用状态。
- **GIF footer**：`render.py` / `server.py` 中 `loading_gif_img_key` 参数链。
- **模型名归一化**：`hermes_feishu_card/model_names.py` + `render.py` 的
  `from .model_names import normalize_model_name`。
- **footer 空值不显示**：`session.py` 的 `model: str = ""`（上游会改回 `"Unknown"`）；
  footer 不再前置 `已完成 · `。
- **emoji-only 应答删卡**：`server.py` 的 `_is_emoji_only()` 分支。
- **生命周期日志**：`server.py` 的 `_card_log()`。
- **timeline 动态展开**：`server.py` 的 `_resolve_timeline_expanded()`；
  `config.py` **不设** `timeline_expanded` 默认值。
- **wide_screen_mode**：`render.py` 卡片 config。

**上游值得吸收的新能力**（视版本而定）：

- v4.3.6+：@提及开关（`interaction_profile_id` / `mentions_enabled`）
- v4.4.1：Hermes 2026-09 facade 分解支持（`install/decomposed.py`）——**0.21 安装的关键**
- v4.4.0+：native command center

### 2.5 合并后验证

```bash
# 1. 确认无残留冲突标记
grep -rn "<<<<<<<\|>>>>>>>" hermes_feishu_card/ tests/ 2>/dev/null

# 2. 语法与导入
python3 -c "from hermes_feishu_card import config, server, render, hook_runtime, session; print('imports OK')"

# 3. 本地修订逐项核对（示例）
grep -A1 "def _thread_id_for_event" hermes_feishu_card/server.py | tail -1   # 应为 return None
grep -c '"conversation_id": chat_id' hermes_feishu_card/hook_runtime.py       # 应为 3
grep -c "_is_emoji_only" hermes_feishu_card/server.py                          # 应 > 0
grep -c "_card_log" hermes_feishu_card/server.py                               # 应 > 0
grep -c "normalize_model_name" hermes_feishu_card/render.py                    # 应 > 0
grep -n 'model: str = ""' hermes_feishu_card/session.py                        # 应存在
grep -c "_resolve_timeline_expanded" hermes_feishu_card/server.py              # 应 > 0
grep -c "loading_gif_img_key" hermes_feishu_card/render.py                     # 应 > 0

# 4. 提交合并
git add -A && git commit --no-edit

# 5. 测试
python3 -m pytest tests/unit -q
```

### 2.6 更新 LOCAL_PATCHES.md

合并提交后，在 `LOCAL_PATCHES.md` 顶部更新"最后更新"版本号，并补充本次合并的
冲突保留记录（哪些本地修订与上游冲突、如何解决的），防止下次合并误丢。

---

## 三、安装到 Hermes

### 3.1 前置检查

```bash
# 诊断：确认 Hermes 版本与插件兼容性
python3 -m hermes_feishu_card.cli doctor --config config.yaml.example \
  --hermes-dir ~/.hermes/hermes-agent
```

关注输出中的 `compatibility` 字段：

- `compatibility: full` → 可直接安装
- `compatibility: unsupported` + `message_handler: missing` → Hermes 大版本不兼容，
  需要先合并上游的适配修订（见 3.4）

### 3.2 正常安装

```bash
python3 -m hermes_feishu_card.cli install --hermes-dir ~/.hermes/hermes-agent --yes
```

### 3.3 安装后的重启

```bash
launchctl kickstart -k gui/$(id -u)/ai.hermes.feishu-card
launchctl kickstart -k gui/$(id -u)/ai.hermes.gateway
launchctl kickstart -k gui/$(id -u)/ai.hermes.gateway-coach
sleep 4
ps aux | grep -E "hermes.*(gateway|feishu-card)" | grep -v grep
```

期望看到 3 个进程：两个 `hermes_cli.main ... gateway run`（default + coach）和
一个 `hermes_feishu_card.runner`（sidecar）。

---

## 四、常见故障与处理

### 4.1 `error: run.py changed since install; refusing to install`

**原因**：Hermes 侧 `gateway/run.py`（或分解后的文件）在本次安装后又被改动，
manifest 记录的校验哈希与当前文件不符。常见于 Hermes 自身被升级。

**处理**：手动重置 Hermes 基线 + 清理过期 manifest：

```bash
cd ~/.hermes/hermes-agent
git checkout -- gateway/run.py gateway/platforms/base.py cron/scheduler.py 2>/dev/null
rm -f .hermes_feishu_card_manifest \
      gateway/run.py.hermes_feishu_card.bak \
      gateway/platforms/base.py.hermes_feishu_card.bak \
      cron/scheduler.py.hermes_feishu_card.bak
cd /Users/luantu/.hermes/feishu-card
python3 -m hermes_feishu_card.cli install --hermes-dir ~/.hermes/hermes-agent --yes
```

### 4.2 `compatibility: unsupported`（锚点缺失）

**原因**：Hermes 升级到大版本（如 0.20 → 0.21），重构了 `gateway/run.py`，
移除了插件依赖的锚点函数（`_handle_message_with_agent`、`_run_agent` 等）。
Hermes 0.21 把 run.py 从单文件拆成 8 个文件（`run_turn.py`、`run_turn_runner.py` 等）。

**处理**：
1. 检查上游是否有对应适配分支/版本（如 `codex/v4.4.1-issue-repairs` 的
   `feat(install): support Hermes 2026-09 facade decomposition (8-file ownership)`）。
2. 合并适配修订后再安装。
3. 安装时可能需要 `--accept-hermes-upgrade`（分解源升级）：

```bash
python3 -m hermes_feishu_card.cli install \
  --hermes-dir ~/.hermes/hermes-agent \
  --accept-hermes-upgrade --yes
```

> ⚠️ 该分支会恢复 topic 支持，与本地"禁用话题"策略冲突。合并后按 2.4 重新应用
> 本地话题禁用 patch。

### 4.3 `error: decomposed source upgrade requires --accept-hermes-upgrade`

**原因**：Hermes 源结构从单文件变为分解的 8 文件，属于受支持的源码替换，
安装器要求显式确认。

**处理**：加 `--accept-hermes-upgrade` 重新安装（见 4.2）。

### 4.4 `--no-repair` 无法绕过不兼容检查

**注意**：`--no-repair` 只跳过"修复"阶段，**不能**绕过 `compatibility: unsupported`
的硬门（`cli.py` 中 `if not detection.supported: return 1`）。Hermes 大版本不兼容
只能通过合并上游适配修订解决，没有合法的强制安装路径。

### 4.5 测试大量失败疑似回归

```bash
python3 -m pytest tests/unit -q --tb=no 2>&1 | grep "^FAILED" | sed 's/\[.*//' | sort -u
```

对照历史基线判断：
- 已知失败集合（如 topic/线程路由测试、native hook 环境测试）→ 非本次回归。
- 与本次合并文件相关的失败 → 检查冲突解决是否正确。
- 用 `git stash && pytest <file> && git stash pop` 对比合并前后的失败集合。

---

## 五、快速检查清单

每次合并 + 安装后，按此清单快速过一遍：

- [ ] `git fetch upstream` 确认是否落后
- [ ] 工作树干净 / 已处理并发改动
- [ ] 合并无未解决冲突（`git diff --name-only --diff-filter=U` 为空）
- [ ] `LOCAL_PATCHES.md` 逐项核对：话题禁用、GIF、model_names、emoji、card_log、
      model 空值、动态 timeline、wide_screen_mode
- [ ] `python3 -c "from hermes_feishu_card import ..."` 导入通过
- [ ] `doctor` 报 `compatibility: full`
- [ ] `install` 成功
- [ ] 三个服务重启后存活
- [ ] 推送 origin：`git push origin main`

---

## 六、参考

- 本地修订清单：`LOCAL_PATCHES.md`
- 上游发布说明：`docs/release-notes-*.md`
- 维护指南：`docs/wiki/maintenance-guide.md`
- 发布流程：`docs/wiki/release-playbook.md`
