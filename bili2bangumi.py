#!/usr/bin/env python3

from collections import defaultdict
from asyncio import get_event_loop, TimeoutError as asyncio_TimeoutError
from itertools import count
from tkinter.constants import N
from webbrowser import open as webbrowser_open
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from aiohttp import ServerConnectionError
from bilibili_api.user import User, BangumiType
from bilibili_api import Credential
from requests import get, post, Timeout, HTTPError


# 基础设置，必填
UID = "你的 UID"

# bilibili_api 设置，选填（开启隐私设置则必填）
SESSDATA = "你的 SESSDATA"
BILI_JCT = "你的 bili_jct"
BUVID3 = "你的 buvid3"

# bangumi oauth2 设置，必填
APP_ID = '你的 App ID'
APP_SECRET = '你的 App Secret'


BANGUMI_DATA_LINK = 'https://cdn.jsdelivr.net/npm/bangumi-data@0.3/dist/data.json'


def get_bili2bgm_map(bangumi_data_link):
    '''构造 Bilibili -> Bangumi 番剧编号映射'''
    bangumi_data = get(bangumi_data_link).json()
    bili2bgm_map = defaultdict(lambda: None)
    for bangumi in bangumi_data['items']:
        bili_id = bgm_id = None
        for site in bangumi['sites']:
            name = site['site']
            if name == 'bilibili':
                bili_id = int(site['id'])
            elif name == 'bangumi':
                bgm_id = site['id']
            else:
                continue
            if bili_id is not None and bgm_id is not None:
                bili2bgm_map[bili_id] = bgm_id
                break
    return bili2bgm_map

# TODO: 重写为生成器


def get_bili_bangumi_data(uid, credential):
    '''获取 Bilibili 番剧数据'''
    user = User(uid=uid, credential=credential)
    loop = get_event_loop()
    bangumi_data = {}
    for pn in count(1):  # 依次获取每一页
        for i in range(3):  # 尝试三次
            try:
                bangumi_data_raw = loop.run_until_complete(user.get_subscribed_bangumis(
                    pn=pn, type_=BangumiType.BANGUMI
                ))['list']
            except (asyncio_TimeoutError, ServerConnectionError):
                continue
            else:
                break
        else:
            raise RuntimeError("网络连接错误")
        if len(bangumi_data_raw) == 0:
            break
        for bangumi in bangumi_data_raw:
            # follow_status => 1: 想看, 2: 在看, 3: 看过
            bangumi_data[bangumi['media_id']] = \
                {1: 'wish', 2: 'do', 3: 'collect'}[bangumi['follow_status']]
        pn += 1
    return bangumi_data


class BgmAuthHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.server.code = parse_qs(urlparse(self.path).query)['code'][0]


def auth_bgm(address, app_id, app_secret):
    server = HTTPServer(address, BgmAuthHTTPRequestHandler)
    webbrowser_open(
        f'https://bgm.tv/oauth/authorize?client_id={app_id}&response_type=code'
    )
    server.handle_request()
    for i in range(3):
        try:
            r = post(
                'https://bgm.tv/oauth/access_token',
                data={
                    'grant_type': 'authorization_code',
                    'client_id': app_id,
                    'client_secret': app_secret,
                    'code': server.code,
                    'redirect_uri': 'http://localhost:3000'
                },
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0)'
                    ' Gecko/20100101 Firefox/89.0'
                },
                timeout=(20, 50)
            ).json()
        except Timeout:
            continue
        else:
            break
    else:
        raise RuntimeError("网络连接错误")
    return f'{r["token_type"]} {r["access_token"]}'


def update_bgm_one_bangumi_data(bangumi, status, bgm_auth_data):
    if bangumi is None:
        return False
    for i in range(3):
        try:
            post(
                f'https://api.bgm.tv/collection/{bangumi}/update',
                data={
                    'status': status
                },
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0)'
                    ' Gecko/20100101 Firefox/89.0',
                    'Authorization': bgm_auth_data
                },
                timeout=(20, 50)
            ).raise_for_status()
        except Timeout:
            continue
        except HTTPError:
            return False
        else:
            return True
    else:
        return False


def update_bgm_bangumi_data(bgm_bangumi_data, bgm_auth_data):
    for bangumi, status in bgm_bangumi_data:
        update_bgm_one_bangumi_data(bangumi, status, bgm_auth_data)


def main():
    bili2bgm_map = get_bili2bgm_map(BANGUMI_DATA_LINK)

    credential = None
    if (
        SESSDATA != "你的 SESSDATA"
        and BILI_JCT != "你的 bili_jct"
        and BUVID3 != "你的 buvid3"
    ):
        credential = Credential(
            sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3
        )
    bili_bangumi_data = get_bili_bangumi_data(UID, credential)
    bgm_auth_data = auth_bgm(('localhost', 3000), APP_ID, APP_SECRET)

    bgm_bangumi_data = dict(map(
        lambda bangumi, status: (
            bili2bgm_map[bangumi], status
        ), bili_bangumi_data.values()
    ))
    update_bgm_bangumi_data(bgm_bangumi_data, bgm_auth_data)


if __name__ == '__main__':
    main()
