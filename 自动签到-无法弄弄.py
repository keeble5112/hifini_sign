# -*- coding: utf-8 -*-

import requests
import re
import traceback
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# ============================  1. 基础配置 (必须修改)  ============================
# 将你的浏览器Cookie字符串粘贴到这里
COOKIES_STR = 'bbs_sid=pvfepm1itbdu7fco3lct1el702; bbs_token=YBwFyLB_2BCgYXddhTNQPedYrTeRZMORBcZDqqpQ2j4g1BAyt8giT56h5noOORq_2BEZJf_2BcQmSqah6oTUylsnrnKLFHdBExpYXs' # <--- 在这里填入你的HiFiNi Cookie

# ============================  2. 邮件通知配置 (必须修改)  ============================
# 发件人邮箱地址 (例如: '123456@qq.com')
SENDER_EMAIL = 'keeble5112@163.com' # <--- 在这里填入你的发件人邮箱
# 发件人邮箱的授权码 (注意：是16位的授权码，不是登录密码！)
SENDER_PASSWORD = 'RPTVk33a4Uww3Ccr' # <--- 在这里填入你最新生成的邮箱授权码
# 收件人邮箱地址 (可以是发件人自己)
RECIPIENT_EMAIL = 'keeble5112@163.com' # <--- 在这里填入你的收件人邮箱
# 邮件服务器地址 (根据你的邮箱类型选择)
# QQ邮箱: 'smtp.qq.com'
# 163邮箱: 'smtp.163.com'
# Gmail: 'smtp.gmail.com'
SMTP_SERVER = 'smtp.163.com'
# =================================================================================

BASE_URL = "https://hifini.com"
SIGN_URL = f"{BASE_URL}/sg_sign.htm"


def parse_cookies(cookie_str: str) -> dict:
    """将浏览器Cookie字符串转换为字典"""
    cookie_dict = {}
    for item in cookie_str.split(';'):
        item = item.strip()
        if not item:
            continue
        try:
            key, value = item.split('=', 1)
            cookie_dict[key.strip()] = value.strip()
        except ValueError:
            pass
    return cookie_dict


def run_checkin() -> str:
    """
    执行HiFiNi签到流程并返回结果消息。
    """
    session = requests.Session()
    session.cookies.update(parse_cookies(COOKIES_STR))
    
    print("--- 开始HiFiNi签到流程 ---")
    
    # --- 第一步: 获取 sign 令牌 ---
    print("1. 正在访问签到页面，获取安全令牌(sign)...")
    try:
        response_get = session.get(SIGN_URL)
        response_get.raise_for_status()
        match = re.search(r'var sign = "([a-f0-9]{64})";', response_get.text)
        
        if not match:
            if "请登录" in response_get.text:
                return "获取令牌失败：Cookie已失效或不正确，请重新获取。"
            return "获取令牌失败：在页面中未找到 sign 令牌，网站可能已更新。"
        
        sign_token = match.group(1)
        print(f"   - 成功获取到 sign: {sign_token[:10]}...")
    except requests.exceptions.RequestException as e:
        return f"获取令牌失败：访问签到页面时发生网络错误: {e}"

    # --- 第二步: 执行签到 ---
    print("\n2. 正在发送签到请求...")
    headers = {
        'Referer': SIGN_URL,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    payload = {'sign': sign_token}

    try:
        response_post = session.post(SIGN_URL, data=payload, headers=headers)
        response_post.raise_for_status()
        result = response_post.json()
        message = result.get('message', '未知响应')
        print(f"   - 服务器响应: {message}")
        return message
    except requests.exceptions.RequestException as e:
        return f"签到请求失败：发送POST请求时发生网络错误: {e}"
    except ValueError:
        return f"签到请求失败：服务器返回非JSON格式内容: {response_post.text}"


def send_email_notification(subject: str, body: str):
    """
    使用 smtplib 发送邮件进行调试。
    """
    print("\n--- 开始邮件发送流程 (底层调试模式) ---")

    # --- 构建邮件内容 ---
    message = MIMEText(body, 'plain', 'utf-8')
    message['From'] = Header(f"HiFiNi签到脚本 <{SENDER_EMAIL}>", 'utf-8')
    message['To'] = Header(f"管理员 <{RECIPIENT_EMAIL}>", 'utf-8')
    message['Subject'] = Header(subject, 'utf-8')
    
    server = None
    try:
        # --- 连接并发送邮件 ---
        print(f"[*] 步骤1: 尝试连接到服务器 {SMTP_SERVER} 在端口 465 (SSL)...")
        server = smtplib.SMTP_SSL(SMTP_SERVER, 465, timeout=10)
        print("   - ✅ 连接成功！")

        # 开启调试模式，会打印出与服务器的详细通信过程
        # 0=不输出, 1=常规输出, 2=更详细输出
        server.set_debuglevel(1)

        print("\n[*] 步骤2: 尝试使用授权码登录...")
        # 注意：这里的第二个参数必须是授权码，而不是邮箱密码
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        print("   - ✅ 登录成功！")

        print("\n[*] 步骤3: 尝试发送邮件...")
        server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], message.as_string())
        print("   - ✅ 邮件发送成功！")

    except smtplib.SMTPAuthenticationError as e:
        print("\n   - ❌ 致命错误：SMTP认证失败！")
        print("   - 错误详情:", e)
        print("   - 这几乎100%意味着你的【授权码】是错误的或已失效。请务必重新生成一个新的授权码。")
        
    except Exception as e:
        print(f"\n   - ❌ 发生未知错误: {e}")
        print(f"   - 错误类型: {type(e)}")

    finally:
        # 无论成功与否，都尝试关闭连接
        if server:
            print("\n[*] 步骤4: 关闭与服务器的连接。")
            server.quit()


if __name__ == '__main__':
    # 检查基本配置是否填写
    if 'xxxx' in COOKIES_STR or 'your_sender_email' in SENDER_EMAIL or '授权码' in SENDER_PASSWORD:
        print("❌ 错误：请先在脚本顶部修改 COOKIES_STR 和邮件相关的配置信息！")
    else:
        final_message = ""
        subject = ""
        try:
            # 执行签到并获取结果
            final_message = run_checkin()

            # 根据结果设置邮件标题
            if "成功" in final_message:
                subject = "✅ HiFiNi 签到成功"
            elif "已签到" in final_message:
                subject = "ℹ️ HiFiNi 重复签到"
            else:
                subject = "❌ HiFiNi 签到失败"
        
        except Exception as e:
            # 捕获意外的程序错误
            final_message = f"脚本执行时发生意外错误！\n\n{traceback.format_exc()}"
            subject = "💥 HiFiNi 签到脚本异常"
        
        # 打印最终结果，方便查看
        print("\n--- 签到流程结束 ---")
        print(f"最终结果: {final_message}")

        # 发送邮件通知
        send_email_notification(subject, final_message)
