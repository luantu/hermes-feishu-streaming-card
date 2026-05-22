# 脚本优化说明

## ✅ 优化完成

已优化 `restart` 和 `update` 脚本，使其不依赖固定目录，方便移植。

---

## 📋 优化内容

### 1. **自动检测脚本所在目录**

**优化前**：
```bash
cd /Users/luantu/.hermes/feishu-card/  # 硬编码路径
```

**优化后**：
```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"  # 自动检测脚本所在目录
```

**优点**：
- ✅ 脚本可以在任意目录运行
- ✅ 自动切换到脚本所在目录
- ✅ 方便移植到其他环境

---

### 2. **智能检测 Python 解释器**

**优化前**：
```bash
PYTHON="/Users/luantu/.hermes/hermes-agent/venv/bin/python3"  # 硬编码路径
```

**优化后**：
```bash
detect_python() {
    # 1. 优先使用脚本目录下的虚拟环境
    if [[ -f "${SCRIPT_DIR}/venv/bin/python3" ]]; then
        echo "${SCRIPT_DIR}/venv/bin/python3"
        return 0
    fi
    
    # 2. 检查常见的 Hermes 虚拟环境
    local hermes_venv="${HERMES_DIR}/venv/bin/python3"
    if [[ -f "$hermes_venv" ]]; then
        echo "$hermes_venv"
        return 0
    fi
    
    # 3. 使用系统 Python
    if command -v python3 &> /dev/null; then
        echo "python3"
        return 0
    fi
    
    error "未找到 Python 解释器"
}
```

**优先级**：
1. 脚本目录下的虚拟环境（`./venv/bin/python3`）
2. Hermes 虚拟环境（`$HERMES_DIR/venv/bin/python3`）
3. 系统 Python（`python3`）

**优点**：
- ✅ 自动选择最佳 Python 环境
- ✅ 支持多种部署方式
- ✅ 无需手动配置

---

### 3. **配置文件路径自动检测**

**优化前**：
```bash
--config config.yaml  # 相对路径，依赖当前工作目录
```

**优化后**：
```bash
CONFIG_FILE="${SCRIPT_DIR}/config.yaml"  # 绝对路径
--config "$CONFIG_FILE"
```

**优点**：
- ✅ 配置文件路径绝对化
- ✅ 不依赖当前工作目录
- ✅ 更可靠

---

### 4. **环境变量支持**

**update 脚本新增**：
```bash
# 可通过环境变量覆盖默认值
HERMES_DIR="${HERMES_DIR:-$HOME/.hermes/hermes-agent}"
```

**使用方式**：
```bash
# 方式 1：使用默认值
./update

# 方式 2：通过环境变量指定
HERMES_DIR=/custom/path ./update

# 方式 3：导出环境变量
export HERMES_DIR=/custom/path
./update
```

**优点**：
- ✅ 灵活配置
- ✅ 支持多环境部署
- ✅ 向后兼容

---

### 5. **错误处理增强**

**新增检查**：
```bash
# 检查配置文件
if [[ ! -f "$CONFIG_FILE" ]]; then
    error "配置文件不存在: $CONFIG_FILE"
fi

# 检查 Hermes 目录
if [[ ! -d "$HERMES_DIR" ]]; then
    warn "Hermes 目录不存在: $HERMES_DIR"
fi

# 检查 upstream 远程仓库
if git remote | grep -q upstream; then
    # 同步上游
else
    warn "未配置 upstream 远程仓库"
fi
```

**优点**：
- ✅ 更友好的错误提示
- ✅ 避免因缺少依赖而失败
- ✅ 提供解决方案提示

---

## 🚀 移植方法

### 方法 1：直接复制

```bash
# 复制整个目录到目标位置
cp -r /path/to/feishu-card /target/path/

# 进入目录
cd /target/path/feishu-card

# 运行脚本
./restart
./update
```

### 方法 2：Git Clone

```bash
# Clone 到任意目录
git clone https://github.com/your/repo.git /any/path/feishu-card

# 进入目录
cd /any/path/feishu-card

# 运行脚本
./restart
./update
```

### 方法 3：符号链接

```bash
# 创建符号链接
ln -s /path/to/feishu-card ~/feishu-card

# 通过链接运行
~/feishu-card/restart
~/feishu-card/update
```

---

## 📊 对比

| 特性 | 优化前 | 优化后 |
|------|--------|--------|
| 目录依赖 | ❌ 硬编码 `/Users/luantu/.hermes/feishu-card/` | ✅ 自动检测脚本所在目录 |
| Python 路径 | ❌ 硬编码 `/Users/luantu/.hermes/hermes-agent/venv/bin/python3` | ✅ 智能检测（支持 3 种方式） |
| 配置文件 | ⚠️ 相对路径 `config.yaml` | ✅ 绝对路径 `${SCRIPT_DIR}/config.yaml` |
| 环境变量 | ❌ 不支持 | ✅ 支持 `HERMES_DIR` 环境变量 |
| 错误处理 | ⚠️ 基础 | ✅ 增强（检查配置、目录、远程仓库） |
| 移植性 | ❌ 需要修改脚本 | ✅ 无需修改，直接复制即可 |

---

## 🎯 使用示例

### 示例 1：标准使用

```bash
# 在脚本所在目录运行
cd ~/.hermes/feishu-card
./restart
```

### 示例 2：从其他目录运行

```bash
# 从任意目录运行（脚本会自动切换到正确目录）
/path/to/feishu-card/restart
```

### 示例 3：自定义 Hermes 目录

```bash
# 通过环境变量指定 Hermes 目录
HERMES_DIR=/custom/hermes ./update
```

### 示例 4：创建虚拟环境

```bash
# 在脚本目录创建虚拟环境
cd ~/.hermes/feishu-card
python3 -m venv venv
source venv/bin/activate
pip install -e .

# 脚本会自动使用虚拟环境中的 Python
./restart
```

---

## 🔧 高级配置

### 1. 自定义 Python 路径

如果需要使用特定的 Python 解释器，可以修改 `detect_python` 函数：

```bash
detect_python() {
    # 添加自定义路径
    if [[ -f "/custom/path/to/python3" ]]; then
        echo "/custom/path/to/python3"
        return 0
    fi
    
    # ... 原有逻辑
}
```

### 2. 自定义配置文件

```bash
# 通过环境变量指定配置文件
CONFIG_FILE=/custom/path/config.yaml ./restart
```

### 3. 调试模式

```bash
# 启用 bash 调试模式
bash -x ./restart
```

---

## ✅ 验证

运行以下命令验证脚本是否正常工作：

```bash
# 1. 检查脚本权限
ls -l restart update

# 2. 检查脚本语法
bash -n restart
bash -n update

# 3. 测试运行（查看输出）
./restart
```

---

## 📝 注意事项

1. **首次使用**：
   - 确保 `config.yaml` 存在
   - 确保 Python 3 已安装
   - 确保脚本有执行权限（`chmod +x restart update`）

2. **虚拟环境**：
   - 脚本会优先使用 `./venv/bin/python3`
   - 如果没有虚拟环境，会使用系统 Python

3. **Hermes 目录**：
   - 默认：`$HOME/.hermes/hermes-agent`
   - 可通过环境变量 `HERMES_DIR` 覆盖

4. **Git 操作**：
   - `update` 脚本需要 Git 环境
   - 需要配置 `upstream` 远程仓库才能同步上游代码

---

## 🎉 总结

优化后的脚本具有以下优点：

- ✅ **完全移植**：无需修改即可在任意目录运行
- ✅ **智能检测**：自动选择最佳 Python 环境
- ✅ **灵活配置**：支持环境变量自定义
- ✅ **错误友好**：提供清晰的错误提示和解决方案
- ✅ **向后兼容**：不影响现有使用方式

现在你可以将 `feishu-card` 目录复制到任意位置，脚本都能正常工作！🚀
