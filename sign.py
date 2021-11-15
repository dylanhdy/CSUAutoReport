# coding=utf-8
import json
import re
import json
import requests
import time

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
    user_status = False
    sign_status = False
    while True:
        time_now = time.localtime()
        time_hour = int(time.strftime('%H', time_now))
        time_min = int(time.strftime('%M', time_now))
        if time_hour > 1 and user_status == False:
            with open('user.json', 'r') as f:
                try:
                    user_list = json.load(f)
                except json.decoder.JSONDecodeError as err:
                    run_err = "files user.json decode error %s" % err
                    return "Failed", run_err, " json 文件格式错误"
            print("成功读取用户信息")
            user_status = True
        if time_hour > 1 and sign_status == False:
            for username, cookie in user_list.items():
                print("发起用户 %s 打卡请求" % username)
                status, data, message = sign(username, cookie)
                print(status, message)
            sign_status = True
        if time_hour == 0 and time_min <= 10:
            user_status = False
            sign_status = False
        time.sleep(60)

if __name__ == '__main__':
    main()