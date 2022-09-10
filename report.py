import re
import json
import string
import requests
import random
import base64
import time
from bs4 import BeautifulSoup
from Crypto.Cipher import AES

def random_string(length, chars=string.digits + string.ascii_letters):
    return ''.join(random.choice(chars) for _ in range(length))

def get_aes_password(password, salt):
    encrypt_iv = random_string(16)
    encrypt_mode = AES.MODE_CBC
    encrypt_text = random_string(64) + str(password)
    fill_block_size = AES.block_size - len(encrypt_text) % AES.block_size
    encrypt_text = encrypt_text + fill_block_size * chr(fill_block_size)
    encrypt_lock = AES.new(salt.encode("utf-8"), encrypt_mode, encrypt_iv.encode('utf-8'))
    ciphered_text = encrypt_lock.encrypt(encrypt_text.encode("utf-8"))
    return base64.standard_b64encode(ciphered_text).decode("utf-8")

def login(username, password):
    # 解析信息门户加密信息
    session = requests.session()
    auth_url = 'https://ca.csu.edu.cn/authserver/login'
    http_result = session.get(auth_url)
    try:
        soup = BeautifulSoup(http_result.text, 'lxml')
        salt = soup.find(id="pwdLoginDiv").find(id="pwdEncryptSalt")["value"]
        exec_ = soup.find(id="pwdLoginDiv").find(id="execution")["value"]
    except TypeError:
        run_err = "BeautifulSoup TypeError"
        return "Failed", run_err, "连接SSO失败(信网中心连接异常)"

    # 发起登录请求
    form_data = {
        "username": username,
        "password": get_aes_password(password, salt),
        "_eventId": "submit",
        "execution": exec_,
        "cllt": "userNameLogin",
        "dllt": "generalLogin",
        "lt": "",
    }
    try:
        http_result = session.post(auth_url, data=form_data)
        http_result.encoding = 'utf-8'
        re_result = re.search("<title>(.*)</title>", http_result.text)
        html_title = re_result.group(1)
    except requests.exceptions.ReadTimeout:
        run_err = "requests.exceptions.ReadTimeout:[%s]" % auth_url
        return "Failed", run_err, "连接SSO失败(信网中心无响应)"
    except requests.exceptions.ConnectionError:
        run_err = "requests.exceptions.ConnectionError:[%s]" % auth_url
        return "Failed", run_err, "连接SSO失败(信网中心无响应)"
    except AttributeError:
        run_err = "Request AttributeError"
        return "Failed", run_err, "连接SSO异常(无法正确解析页面)"
    # if html_title == "个人中心":
    #     return "Success", session.cookies.get_dict(), "成功获取用户 cookie"
    # elif html_title == "统一身份认证平台":
    #     run_err = "user %s imformation is incorrect" % username
    #     return "Failed", run_err, "连接SSO失败(用户信息错误)"
    # else:
    #     run_err = "Unknown html title: " + html_title
    #     return "Failed", run_err, "未知错误，请向作者反馈"
    if html_title == "统一身份认证平台":
        run_err = "user %s imformation is incorrect" % username
        return "Failed", run_err, "连接SSO失败(用户信息错误)"
    else:
        return "Success", session.cookies.get_dict(), "成功获取用户 cookie"

def sign(username, cookie):
    # 解析打卡状态
    session = requests.session()
    sign_url = 'https://wxxy.csu.edu.cn/ncov/wap/default/index'
    http_result = session.get(sign_url, cookies=cookie)
    regex = r"hasFlag: '(.*)',"
    re_result = re.search(regex, http_result.text)
    if re_result is None:
        return "content_error", http_result.text, "缺少打卡标记"
    flag_data = re_result.group(1)
    if flag_data == "1":
        return "Failed", "用户 %s 请求今日已提交" % username, "今日已提交"

    # 解析历史数据
    regex = r'oldInfo: (.*),'
    re_result = re.search(regex, http_result.text)
    if re_result is None:
        return "content_error", "Missing history data", "缺少历史数据"
    old_data = json.loads(re_result.group(1))

    # 发起打卡请求
    sign_url = 'https://wxxy.csu.edu.cn/ncov/wap/default/save'
    try:
        http_result = session.post(sign_url, data=old_data, timeout=(3, 10))
    except requests.exceptions.ReadTimeout:
        return "connect_error", "ReadTimeout at step 2", "自动打卡超时"
    except requests.exceptions.ConnectionError:
        return "connect_error", "ConnectionError at step 2", "自动打卡失败"
    sign_res = json.loads(http_result.text)
    if sign_res["e"] == 0:
        return "Success", "用户 %s 提交信息成功" % username, "提交信息成功"
    elif sign_res["e"] == 1 and sign_res["m"] == "今天已经填报了":
        return "Success", "用户 %s 信息今天已经填报" % username, "信息今天已经填报"
    return "response_error", "Unknown situation", sign_res["m"]

def main():
    report_status = False
    while True:
        time_now = time.localtime()
        time_hour = int(time.strftime('%H', time_now))
        time_min = int(time.strftime('%M', time_now))
        if time_hour >= 1 and report_status == False:
            with open('user.json', 'r') as f:
                try:
                    user = json.load(f)
                    username = user['username']
                    password = user['password']
                except json.decoder.JSONDecodeError as err:
                    run_err = "files user.json decode error %s" % err
                    return "Failed", run_err, " json 文件格式错误"
            print("成功读取用户信息")
            status, cookie, message = login(username, password)
            print(status, message)
            if(status != "Success"):
                print(status, message)
                return
            status, data, message = sign(username, cookie)
            print(status, message)
            report_status = True
        if time_hour == 0 and time_min <= 10:
            report_status = False
        time.sleep(60)

if __name__ == '__main__':
    main()