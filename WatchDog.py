import socket
import subprocess
import time
import requests
import psutil

# ================= 配置区 =================
# 1. 校园网认证配置
AUTH_URL = "http://10.0.1.5"
USERNAME = "学号"
PASSWORD = "密码"
ISP_TYPE = "网络选择"  # 电信 @telecom, 联通 @unicom, 移动 @cmcc

# 2. 网络接口名称 (在"控制面板-网络连接"中查看)
WIRED_INTERFACE_NAME = "有线网卡连接名称" # 例如，"以太网 2"

# 3. 路由器 WiFi 
# 路由器SSID名称
WIFI_SSID = "路由器SSID名称" # 例如，"Intelligence-Lab"
# 路由器网关IP
WIFI_GATEWAY = "192.168.XX.XX"


# 4. 运行参数
CHECK_INTERVAL = 10  # 外网检测周期


# ==========================================

def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}")


def get_host_ip():
    """
    获取本机连接外网的IPv4地址。
    这是Dr.COM认证中至关重要的一步，服务器会校验请求中的IP是否与来源IP一致。
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 不需要真正连接成功，只需要路由
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception as e:
        log(f"无法获取本机IP: {e}")
        return None
    finally:
        s.close()
    return ip


def run_wired_authentication():
    """
    执行有线网络认证 (GUET Dr.COM 协议)
    参考 AutoLoginGuet 的逻辑，针对 10.0.1.5 发送认证请求。
    """
    host_ip = get_host_ip()
    if not host_ip:
        log("未检测到有效IP地址，跳过认证。")
        return False

    # 认证服务器地址 (GUET 有线网络标准地址)
    url = AUTH_URL + "/drcom/login"

    # 构造请求参数
    # 参考 AutoLoginGuet 及通用 Dr.COM 协议：
    # DDDDD: 账号
    # upass: 密码
    # 0MKKey: 通常固定为 123456
    # v6ip: IPv6地址 (可选，通常留空)
    params = {
        "callback": "dr1003",
        "DDDDD": USERNAME + ISP_TYPE,  # 账号+运营商类型
        "upass": PASSWORD,
        "0MKKey": "123456",
        "R1": "0",
        "R2": "",
        "R3": "0",
        "R6": "0",
        "para": "00",
        "v6ip": "",
        "terminal_type": "1",
        "lang": "zh-cn",
        "jsVersion": "4.1",
        "v": "1010"
    }

    # 请求头，模拟浏览器行为
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Referer": AUTH_URL + "/",
        "Connection": "keep-alive"
    }

    try:
        log(f"正在尝试有线认证... 账号: {USERNAME}{ISP_TYPE}, IP: {host_ip}")
        response = requests.get(url, params=params, headers=headers, timeout=5)

        # 检查响应内容
        # 成功通常返回 "result":1
        # 失败通常返回 "result":0 和 "msg"
        content = response.text

        if '"result":1' in content:
            log("有线网络认证成功！")
            return True
        elif '"result":0' in content:
            # 尝试提取错误信息 (简单的字符串查找，避免引入复杂的解析库)
            msg_start = content.find('"msg":"') + 7
            msg_end = content.find('"', msg_start)
            msg = content[msg_start:msg_end] if msg_start > 6 and msg_end > msg_start else "未知错误"

            # 特殊情况：如果提示"已登录"或类似信息，也可以视为成功
            if "已登录" in msg or "can not modify" in msg or "已经在线" in msg:
                log("检测到设备已在线，无需重复登录。")
                return True

            log(f"认证失败: {msg}")
            return False
        else:
            log(f"收到未知的响应格式: {content[:100]}...")
            return False

    except requests.exceptions.RequestException as e:
        log(f"认证请求发送异常: {e}")
        return False


# 断开连接
def disconnect_wifi():
    """
    断开当前WiFi连接
    返回: True=成功, False=失败
    """
    try:
        # 尝试断开连接
        cmd = 'netsh wlan disconnect'
        result = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.DEVNULL,  # 不捕获输出
            stderr=subprocess.DEVNULL,  # 不捕获错误
            timeout=5
        )

        # 等待断开生效
        time.sleep(2)
        return result.returncode == 0
    except Exception as e:
        log(f"断开WiFi异常: {e}")
        return False


# 连接SSID
def connect_wifi(SSID):
    result = subprocess.call(
        ['ping', '-n', '1', '-w', '2000', WIFI_GATEWAY],
        stdout=subprocess.DEVNULL,  # 不显示 Ping 的具体输出
        stderr=subprocess.DEVNULL
    )

    if result != 0:
        log(f"[!] 检测到与网关 {WIFI_GATEWAY} 断开连接！")
        log(f"[*] 正在尝试重连 WiFi: {SSID} ...")

        # 2. 执行 Windows 连接 WiFi 命令
        # 语法: netsh wlan connect name="SSID名称"
        connect_cmd = f'netsh wlan connect name="{SSID}"'
        subprocess.run(connect_cmd, shell=True)

        # 等待几秒让连接建立，避免连续报错
        time.sleep(10)


# ping网络检查
def check_ping(target, source_ip=None):
    cmd = ['ping', '-n', '1', '-w', '2000']

    if source_ip:
        cmd.extend(['-S', source_ip])

    cmd.append(target)

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False  # 提高安全性
        )
        return result.returncode == 0
    except Exception:
        return False


def get_ip_by_name(adapter_name_keyword="以太网"):
    addrs = psutil.net_if_addrs()
    for interface_name, interface_addresses in addrs.items():
        # 匹配名称，例如 "以太网" 或 "Ethernet"
        if adapter_name_keyword in interface_name:
            for address in interface_addresses:
                # 确保是 IPv4 地址
                if address.family == 2:  # AF_INET
                    return address.address
    return None


# 看门狗逻辑
def watchdog_logic():
    log("网络看门狗已启动")
    while True:
        # 1. 检测外网连通性 (有线网卡)
        WIRED_IP = get_ip_by_name(WIRED_INTERFACE_NAME)
        if not check_ping("www.baidu.com", WIRED_IP) and not check_ping("www.qq.com", WIRED_IP):
            log("[-] 校园网准备有线网认证")

            # A. 断开无线网，防止路由冲突和认证页无法弹出
            if check_ping(WIFI_GATEWAY):
                disconnect_wifi()

            # B. 执行认证逻辑
            if not check_ping(WIFI_GATEWAY):
                run_wired_authentication()

            # C. 等待几秒后再次检查
            time.sleep(5)
            if check_ping("www.baidu.com", WIRED_IP) or check_ping("www.qq.com", WIRED_IP):
                log("[√] 校园网连接成功")
                connect_wifi(WIFI_SSID)
            else:
                log("[X] 校园网连接失败")
        else:
            # 检查实验室网关是否通畅
            if not check_ping(WIFI_GATEWAY):
                connect_wifi(WIFI_SSID)
                log(f"[X] 实验室网关 {WIFI_GATEWAY} 连接失败，尝试连接 WiFi: {WIFI_SSID}")

        time.sleep(CHECK_INTERVAL)


# ================= 入口点 =================

def main():
    watchdog_logic()


if __name__ == '__main__':
    main()