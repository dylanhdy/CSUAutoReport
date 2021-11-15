# coding=utf-8
import re
import json
import string
import requests
import random
import base64
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
    if html_title == "个人中心":
        return "Success", session.cookies.get_dict(), "成功获取用户 cookie"
    elif html_title == "Unified identity authentication platform":
        run_err = "user %s imformation is incorrect" % username
        return "Failed", run_err, "连接SSO失败(用户信息错误)"
    else:
        run_err = "Unknown html title: " + html_title
        return "Failed", run_err, "未知错误，请向作者反馈"

def update(username, cookie):
    # 打开 cookie 文件
    with open('user.json', 'r') as f:
        # 文件丢失报错
        try:
            user_list = json.load(f)
        except json.decoder.JSONDecodeError as err:
            run_err = "files user.json decode error %s" % err
            return "Failed", run_err, "用户 json 格式错误"
        if username in user_list:
            run_err = "user %s 's cookie has already existed" % username
            return "Failed", run_err, "用户 cookie 已存在"

    # 更新用户 cookie
    user_list[username] = cookie
    with open('user.json', 'w') as f:
        return "Success", json.dump(user_list, f, indent=4), "成功更新 cookie"

def main():
    while True:
        username = input("中南大学学工号：")
        password = input("信息门户密码：")
        status, data, message = login(username, password)
        print(status, message)
        if(status == "Failed" and message == "连接SSO失败(用户信息错误)"):
            continue
        break
    if(status == "Success"):
        status, data, message = update(username, data)
        print(status, message)

if __name__ == '__main__':
    main()