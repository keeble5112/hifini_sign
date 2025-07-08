import requests
import re
import json
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime

# ============================  1. 网站配置  ============================
# 将你的新版网站Cookie字符串粘贴到这里。
COOKIES_STR = 'bbs_sid=fhur6maj38jg6g9a2sjhdpm96g; __51cke__=; _wish_accesscount_visited=1; bbs_token=5_2FqvFgKCi8_2FM06pC1DrMMKtwPKtvjcE6nkapdGZdRtnHSMY6; postlist_orderby_uid=; __tins__21444353=%7B%22sid%22%3A%201751985017956%2C%20%22vd%22%3A%2043%2C%20%22expires%22%3A%201751988130178%7D; __51laig__=43'

# ============================  2. 邮件通知配置  ============================
# 设置为 False 可禁用邮件通知功能
EMAIL_ENABLED = True

# --- SMTP服务器配置 ---
SMTP_SERVER = 'smtp.163.com'
SMTP_PORT = 465

# --- 发件人邮箱信息 ---
SENDER_EMAIL = 'keeble5112@163.com'
SENDER_PASSWORD = 'RPTVk33a4Uww3Ccr' # 授权码

# --- 收件人邮箱信息 ---
RECIPIENT_EMAIL = 'keeble5112@163.com'

# ============================  脚本核心代码 (通常无需修改)  ============================

# --- 关键修改：定义一个更像浏览器的请求头 ---
HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    # 'X-Requested-With' 只在POST时需要，所以单独处理
}

BASE_URL = "https://www.hifini.com.cn"
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

def check_login_status(session: requests.Session) -> (bool, str):
    """访问签到页面，检查登录状态，并返回状态和消息"""
    print("1. 正在访问签到页面，检查登录状态...")
    try:
        # --- 关键修改：在GET请求中也加入Headers ---
        response = session.get(SIGN_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()

        if 'user-logout.htm' in response.text:
            msg = "✅ 登录状态正常。"
            print(f"   - {msg}")
            return True, msg
        else:
            msg = "❌ 登录状态异常！Cookie可能已失效，请重新获取。"
            print(f"   - {msg}")
            return False, msg

    except requests.exceptions.RequestException as e:
        msg = f"❌ 访问签到页面失败: {e}"
        print(f"   - {msg}")
        return False, msg

def do_sign_in(session: requests.Session) -> str:
    """发送POST请求完成签到，并返回结果消息"""
    print("\n2. 正在发送签到请求...")
    # 复制全局headers，并添加POST请求特有的'X-Requested-With'
    post_headers = HEADERS.copy()
    post_headers['Referer'] = SIGN_URL
    post_headers['X-Requested-With'] = 'XMLHttpRequest'
    
    try:
        response = session.post(SIGN_URL, data={}, headers=post_headers, timeout=15)
        response.raise_for_status()
        
        try:
            result = response.json()
            message = result.get('message', '未知响应')
            if result.get('code') == 0:
                msg = f"✅ 签到成功！服务器返回: {message}"
            else:
                msg = f"ℹ️  操作完成。服务器返回: {message}"
        except json.JSONDecodeError:
            msg = f"❌ 服务器返回的不是有效的JSON格式。响应内容: {response.text[:200]}" # 记录部分响应内容
        
        print(f"   - {msg}")
        return msg

    except requests.exceptions.RequestException as e:
        msg = f"❌ 发送签到请求失败: {e}"
        print(f"   - {msg}")
        return msg


def send_email(subject: str, body: str):
    """发送邮件通知"""
    if not EMAIL_ENABLED:
        print("\n邮件通知功能已禁用。")
        return

    print("\n3. 正在发送邮件报告...")
    
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['From'] = Header(f"HiFiNi签到助手 <{SENDER_EMAIL}>", 'utf-8')
    msg['To'] = Header(f"管理员 <{RECIPIENT_EMAIL}>", 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')

    try:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, [RECIPIENT_EMAIL], msg.as_string())
        server.quit()
        print(f"   - ✅ 邮件报告已成功发送至 {RECIPIENT_EMAIL}")
    except Exception as e:
        print(f"   - ❌ 邮件发送失败: {e}")
        print("   -   请检查SMTP配置、邮箱地址和授权码是否正确。")


if __name__ == '__main__':
    if not COOKIES_STR or 'bbs_sid' not in COOKIES_STR:
        print("错误：请先在脚本顶部填写你的 `COOKIES_STR`。")
        exit()
    
    if EMAIL_ENABLED and ('keeble5112' in SENDER_EMAIL or 'RPTV' in SENDER_PASSWORD):
        print("提示：您正在使用示例邮件配置，请确保已替换为您自己的信息。")
    
    report_lines = []
    
    session = requests.Session()
    session.cookies.update(parse_cookies(COOKIES_STR))

    is_logged_in, login_message = check_login_status(session)
    report_lines.append(login_message)

    if is_logged_in:
        sign_in_message = do_sign_in(session)
        report_lines.append(sign_in_message)

    today_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    final_report_str = "\n".join(report_lines)
    
    if "✅" in final_report_str and "❌" not in final_report_str:
        email_subject = f"✅ HiFiNi 签到成功 - {today_str}"
    elif "❌" in final_report_str:
        email_subject = f"❌ HiFiNi 签到失败 - {today_str}"
    else:
        email_subject = f"ℹ️ HiFiNi 签到报告 - {today_str}"

    email_body = f"HiFiNi 自动签到任务报告：\n\n"
    email_body += "================================\n"
    email_body += final_report_str
    email_body += "\n================================\n\n"
    email_body += f"报告生成时间: {today_str}"

    send_email(email_subject, email_body)
    print("\n脚本执行完毕。")
