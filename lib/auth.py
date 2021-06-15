#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import re
import socket
import webbrowser

import requests

"""
Bangumi Oauth2 授权

@File    :   auth.py
@Time    :   2021/06/15 20:19:43
@Author  :   SINC
"""


def auth_bgm(client_id: str, client_secret: str, redirect_uri: str = "http://localhost:3000") -> str:
    """Bangumi Oauth 2 授权码方式授权.

    参考[bangumi-api 用户授权机制](https: // github.com/bangumi/api/blob/master/docs-raw/How-to-Auth.md).

    Args:
        client_id (str): 配置文件中设置
        client_secret (str): 配置文件中设置
        redirect_uri (str, optional): 配置文件中设置. Defaults to "http://localhost:3000".

    Returns:
        str: Access Token
    """

    auth_url = 'https://bgm.tv/oauth/authorize?client_id=' + \
        client_id + '&response_type=code'

    try:
        webbrowser.open(url=auth_url, new=0)
    except:
        pass

    payload = {'grant_type': 'authorization_code',
               'client_id': client_id, 'client_secret': client_secret, 'code': '', 'redirect_uri': ''}

    payload['code'] = runServer()

    payload['redirect_uri'] = redirect_uri

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36 Edg/83.0.478.58'
    }
    r = requests.post('https://bgm.tv/oauth/access_token',
                      data=payload, headers=headers).json()

    return r['token_type']+' '+r['access_token']


def runServer(server_address=('localhost', 3000)):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(server_address)
    sock.listen(1)
    print("本地监听服务器已开启，请在浏览器中同意授权...")
    while True:
        connection = sock.accept()[0]
        try:
            data = connection.recv(1024)
        finally:
            code = re.findall('code=(.*?) ', data.decode('utf-8', 'ignore'))
            print("已获取到Code：" + code[0])
            connection.close()
            return str(code[0])
