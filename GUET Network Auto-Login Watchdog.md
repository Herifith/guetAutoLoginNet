# GUET Network Watchdog (Python)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue) ![Platform](https://img.shields.io/badge/Platform-Windows-win)

## 简介 (Introduction)

这是一个**桂电 (GUET)** 校园网有线连接上网认证的 Python 自动化脚本。

主要解决以下问题：
1.  **自动认证**：针对有线网络（Dr.COM 网页认证），实现掉线自动重连。
2.  **双网共存**：在连接有线校园网的同时，保持实验室/宿舍路由器的无线 WiFi 连接（用于局域网互通或作为备用网络）。
3.  **服务化运行**：配合 `nssm` 可在 Windows 11 下作为后台服务运行，实现**开机即自动认证**，无需登录系统桌面。

## 功能特性 (Features)

* **智能检测**：定时检测外网连通性（Ping 百度/QQ）。
* **路由防冲突**：在进行有线网认证时，自动临时断开 WiFi，防止因默认路由优先级导致认证流量走错网卡而失败。
* **WiFi 保活**：有线网正常时，持续监控并维持 WiFi 连接。
* **多运营商支持**：支持电信、联通、移动等不同 ISP 类型的账号后缀配置。
* **轻量级**：基于 Python `requests` 和 `subprocess` 实现。

## 环境依赖 (Requirements)

* Windows 10 / 11
* Python 3.x
* 第三方库：
    ```bash
    pip install requests psutil
    ```

## 配置说明 (Configuration)

在使用前，请使用文本编辑器打开 `WatchDog.py`，并在顶部的 `配置区` 填入您的个人信息：

```python
# ================= 配置区 =================
# 1. 校园网认证配置
AUTH_URL = "[http://10.0.1.5](http://10.0.1.5)"        # 认证服务器地址（通常无需修改）
USERNAME = "您的学号"                # 示例: "2100300xxx"
PASSWORD = "您的密码"                # 校园网密码
ISP_TYPE = "@telecom"               # 运营商后缀: @telecom, @unicom, @cmcc, 或空字符串

# 2. 网络接口名称
# 请在 "控制面板 -> 网络和共享中心 -> 更改适配器设置" 中查看有线网卡的具体名称
WIRED_INTERFACE_NAME = "以太网"      # 注意：Win11 可能显示为 "Ethernet" 或 "以太网 2"

# 3. 路由器 WiFi 配置
WIFI_SSID = "Lab-WiFi-Name"         # 实验室/宿舍 WiFi 名称
WIFI_GATEWAY = "192.168.1.1"        # 路由器的网关 IP (用于检测连接状态)

# 4. 运行参数
CHECK_INTERVAL = 10                 # 检测周期(秒)
# ==========================================
```

## 安装与使用 (Installation & Usage)

### 方式一：直接运行 (调试用)

在 CMD 或 PowerShell 中运行：

Bash

```
python WatchDog.py
```

*此时窗口不能关闭，适合初次运行测试配置是否正确。*

### 方式二：配置为 Windows 服务 (推荐)

使用 `nssm` 将脚本注册为系统服务，实现开机自启（无需用户登录）。

#### 1. 下载 NSSM

下载 [NSSM (Non-Sucking Service Manager)](https://nssm.cc/download)，解压并将 `win64` 目录下的 `nssm.exe` 复制到方便的路径（或添加到环境变量）。

#### 2. 安装服务

以**管理员身份**运行 CMD/PowerShell，执行以下命令：

Bash

```
nssm install GuetNetDog
```

#### 3. 填写参数

在弹出的 GUI 界面中填写：

- **Application 选项卡**:
  - **Path**: 选择您的 python解释器路径 (例如 `C:\Windows\py.exe` 或 Anaconda 的 `python.exe`)
  - **Startup directory**: 脚本所在的文件夹路径
  - **Arguments**: 填写脚本的绝对路径 (例如 `D:\Scripts\WatchDog.py`)
- **I/O 选项卡 (可选，推荐配置用于查看日志)**:
  - **Output (stdout)**: `D:\Scripts\service.log`
  - **Error (stderr)**: `D:\Scripts\service.log`

点击 **Install service** 完成注册。

#### 4. 启动服务

Bash

```
nssm start GuetNetDog
```

或者在任务管理器的“服务”选项卡中找到 `GuetNetDog` 并启动。

------

## 工作流程逻辑

1. **检测外网**：通过有线网卡 Ping `www.baidu.com`。
2. **如果网络不通**：
   - **Step A**: 强制断开当前 WiFi 连接（避免认证包走无线网关）。
   - **Step B**: 获取本机有线 IP，构造 Dr.COM 请求包进行认证。
   - **Step C**: 认证成功后，重新连接指定的 WiFi。
3. **如果网络通畅**：
   - 检查 WiFi 是否连接，若未连接则尝试重连。
4. 每隔 `CHECK_INTERVAL` 秒重复上述过程。

## 致谢 (Acknowledgements)

本项目的认证逻辑（User-Agent 模拟、参数构造）参考了以下开源项目，特此感谢：

- [ReRokutosei/AutoLoginGuet](https://www.google.com/search?q=https://github.com/ReRokutosei/AutoLoginGuet) - GUET 校园网自动登录工具 (Rust 实现)

## 免责声明

本脚本仅供学习交流及个人使用，请勿用于非法用途。使用本脚本产生的任何网络流量费用及后果由使用者自行承担。