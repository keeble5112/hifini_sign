import requests
import re
import json

# ============================  你需要修改的地方  ============================
# 将你的浏览器Cookie字符串粘贴到这里。获取方法见代码下方的说明。
COOKIES_STR = 'bbs_sid=pvfepm1itbdu7fco3lct1el702; bbs_token=YBwFyLB_2BCgYXddhTNQPedYrTeRZMORBcZDqqpQ2j4g1BAyt8giT56h5noOORq_2BEZJf_2BcQmSqah6oTUylsnrnKLFHdBExpYXs'
# ========================================================================

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
            print(f"无法解析Cookie项: {item}")
    return cookie_dict

def get_sign_token(session: requests.Session) -> str:
    """
    访问签到页面，获取动态的 sign 令牌。
    """
    print("1. 正在访问签到页面，获取安全令牌(sign)...")
    try:
        response = session.get(SIGN_URL)
        response.raise_for_status() # 如果请求失败 (如 404, 500), 会抛出异常

        # 使用正则表达式从JavaScript代码中提取sign值
        # 匹配模式: var sign = "一个64位的十六进制字符串";
        match = re.search(r'var sign = "([a-f0-9]{64})";', response.text)
        
        if match:
            sign_token = match.group(1)
            print(f"   - 成功获取到 sign: {sign_token[:10]}...") # 只显示前10位，保护隐私
            return sign_token
        else:
            print("   - 错误：在页面中未找到 sign 令牌。可能页面结构已更新或Cookie已失效。")
            if "请登录" in response.text:
                print("   - 提示: 响应内容中包含'请登录'，请检查Cookie是否正确或过期。")
            return None

    except requests.exceptions.RequestException as e:
        print(f"   - 错误：访问签到页面失败: {e}")
        return None

def do_sign_in(session: requests.Session, sign_token: str):
    """
    发送带有 sign 令牌的 POST 请求来完成签到。
    """
    print("\n2. 正在发送签到请求...")
    
    # 模仿浏览器行为，带上必要的请求头
    headers = {
        'Referer': SIGN_URL,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest' # 很多jQuery的ajax请求会带这个头
    }
    
    payload = {
        'sign': sign_token
    }

    try:
        response = session.post(SIGN_URL, data=payload, headers=headers)
        response.raise_for_status()

        # HiFiNi 的响应是JSON格式的
        try:
            result = response.json()
            # result 格式通常是 {'code': 0, 'message': '签到成功...'}
            # 或者 {'code': -1, 'message': '您已签到...'}
            code = result.get('code')
            message = result.get('message')

            print(f"   - 服务器响应: {message}")
            if code == 0:
                print("   - ✅ 签到成功！")
            else:
                print("   - ℹ️  签到操作完成（可能已签到或有其他提示）。")

        except json.JSONDecodeError:
            print("   - 错误：服务器返回的不是有效的JSON格式。")
            print(f"   - 原始响应内容: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"   - 错误：发送签到请求失败: {e}")


if __name__ == '__main__':
    if not COOKIES_STR or 'xxxx' in COOKIES_STR:
        print("错误：请先在脚本中填写你的Cookie字符串 `COOKIES_STR`。")
    else:
        # 创建一个Session对象，它能自动管理和持久化Cookie
        session = requests.Session()
        session.cookies.update(parse_cookies(COOKIES_STR))
        
        # 第一步：获取 sign 令牌
        sign_token = get_sign_token(session)

        # 第二步：如果成功获取到令牌，则执行签到
        if sign_token:
            do_sign_in(session, sign_token)