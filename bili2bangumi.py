#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""
bilibili动画观看数据导入bangumi

@File    :   bili2bangumi.py
@Time    :   2021/02/01 16:49:46
@Author  :   snc 
"""

import json
import logging

import requests
from bilibili_api import Verify
from bilibili_api.user import get_bangumi_g

# 使用bilibili-api库
# 获取观看数据, 如果不公开需要使用库中 Verify 给予权限

# bilibili api config
uid = 1  # bilibili 用户id(整型), 必填
sessdata = ""  # verify 字段
csrf = ""  # verify 字段

# bangumi oauth2 config
client_id = ''  # 必填
client_secret = ''  # 必填
redirect_uri = 'http://localhost'  # 回调地址，必填


class BangumiTransfer(object):
    """动画番组信息转移(bilibili=>bangumi)
    """
    cdn_bangumi_data = "https://cdn.jsdelivr.net/npm/bangumi-data@0.3/dist/data.json"
    bgm_api = 'https://api.bgm.tv'
    bangumi_data = None

    def __init__(self, uid, verify, bgm_token):
        """初始化

        Args:
            uid (int): B站用户uid
            verify (bilibili_api.Verify): bilibili_api库Verify类,登录验证
            auth_bgm (str): bangumi授权
        """
        self.uid = uid
        self.verify = verify
        self.bgm_token = bgm_token

    def main(self):
        """主程序运行,开始转移,只将已看过的转移到bgm
        """
        failed_bangumi = list()
        updated_bangumi = list()
        try:
            with open('updated.json', 'r', encoding='utf-8') as f:
                updated_bangumi = json.load(f)
        except IOError:
            pass

        updated_bangumi = []  # 已更新bangumi

        self.bangumi_data = requests.get(self.cdn_bangumi_data).json()

        # 用bilibili_api提供的get_bangumi_g获得追番数据
        for bangumi in get_bangumi_g(self.uid, 'bangumi', self.verify):
            if bangumi['title'] in updated_bangumi:
                continue
            if bangumi['follow_status'] == 3:
                logging.info('{} 正在更新...'.format(
                    bangumi['title']))  # TODO 显示输出
                bgm_id = self.__get_bgm_id(bangumi)
                if bgm_id:
                    if self.__update_bgm(bgm_id):
                        updated_bangumi.append(bangumi['title'])
                        logging.info('{} 更新完成!'.format(bangumi['title']))
                    else:
                        logging.warning('{} 更新失败!'.format(bangumi['title']))
                else:
                    failed_bangumi.append(bangumi['title'])
                    logging.warning(
                        "{} 无法获取bangumi(番组计划)条目id!".format(bangumi['title']))

        logging.info('以下番组更新失败:', failed_bangumi)
        with open('updated.json', 'w', encoding='utf-8') as f:
            json.dump(updated_bangumi, f, ensure_ascii=False)

    def __update_bgm(self, id):
        """更新或创建bgm(番组计划)条目,并设置为看过

        Args:
            id (str): bgm条目id

        Returns:
            bool: 布尔值, 是否更新成功
        """
        update_url = "https://api.bgm.tv/collection/{}/update".format(
            id)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36 Edg/83.0.478.58',
            'AUthorization': self.bgm_token
        }
        payload = {'status': 'collect'}
        try:
            r = requests.post(update_url, headers=headers,
                              data=payload, timeout=(20, 50))
        except requests.Timeout:
            return False
        if r.status_code == 200:
            return True
        else:
            return False

    def __get_bgm_id(self, bili_bangumi):

        bili_id = None
        for item in self.bangumi_data['items']:
            for site in item['sites']:
                if site['site'] == 'bangumi':
                    bgm_id = site['id']
                elif site['site'] == 'bilibili':
                    bili_id = site['id']
            if bili_id and bili_bangumi['media_id'] == int(bili_id):
                return bgm_id


def auth_bgm():
    """bgm oauth2授权

    因为需要使用bangumi api,bangumi api又只提供了授权码模式,
    所以需要获取client_id,client_secret.
    """
    global client_id, client_secret, redirect_uri

    auth_url = 'https://bgm.tv/oauth/authorize?client_id=' + \
        client_id + '&response_type=code'
    print("访问该地址并同意授权:\n"+auth_url)

    payload = {'grant_type': 'authorization_code',
               'client_id': client_id, 'client_secret': client_secret, 'code': '', 'redirect_uri': ''}

    payload['code'] = input(
        '输入返回授权码(eg. https://a.com/callback?code=AUTHORIZATION_CODE):\n')

    payload['redirect_uri'] = redirect_uri

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36 Edg/83.0.478.58'
    }
    r = requests.post('https://bgm.tv/oauth/access_token',
                      data=payload, headers=headers).json()
    # print(r)
    print(r['token_type']+' '+r['access_token'])
    return r['token_type']+' '+r['access_token']


def main():
    global uid, sessdata, csrf

    # bgm_token = ""  # 必填
    bgm_token = auth_bgm()

    verify = Verify(sessdata, csrf)

    bgmtran = BangumiTransfer(uid, verify, bgm_token)
    bgmtran.main()


if __name__ == '__main__':
    main()
