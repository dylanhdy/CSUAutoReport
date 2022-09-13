# CSUAutoReport

中南大学自动健康打卡脚本

作者：[@DavidHuang](https://github.com/CrazyDaveHDY)

## 特点

- 支持新版本的中南大学统一身份认证平台
- 解析上一次打卡的信息作为当天的打卡信息

## 安装
### Python3
该项目需要 Python3，可以从 [Python 官网](https://www.python.org/) 下载并安装

### Repo
点击右上角的 `Clone or download` 下载该项目至本地

对于 git 命令行：
```console
$ git clone https://github.com/CrazyDaveHDY/CSUAutoSelect.git
```

### 依赖
安装依赖软件包，在命令行中运行：
```console
$ pip3 install -r requirements.txt
```

## 运行
修改 user.json 文件，其中 username 为学工号，password 为统一身份认证平台密码

进入项目根目录，命令行中运行
```console
$ python3 report.py
```

自动打卡需要脚本一直运行，脚本会在本地时间 1:00 时进行健康打卡。

## 许可协议

CSUAutoReport [GPL-3.0 License](https://github.com/CrazyDaveHDY/CSUAutoReport/blob/main/LICENSE)