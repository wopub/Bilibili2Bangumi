#!/usr/bin/env python
# -*- encoding: utf-8 -*-


"""
配置文件

@File    :   config.py
@Time    :   2021/06/15 20:07:39
@Author  :   SINC
"""


class Config(object):

    # bilibili api config
    # 如果观看数据未公开，则需要设置 SESSDATA 和 CSRF
    UID: int = 12345                    # Bilibili 用户ID，必填
    SESSDATA: str = ""  # 填入 sessdata，选填
    CSRF: str = ""          # 填入 csrf ，选填

    # bangumi oauth2 config
    CLIENT_ID: str = '此处填入 App ID'          # 必填，填入 App ID
    CLIENT_SECRET: str = '此处填入 App Secret'  # 必填，填入 App Secret
