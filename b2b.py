#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from bilibili_api import Verify

from config import Config
from lib.auth import auth_bgm
from lib.migrate import BangumiTransfer

"""
运行此程序开始迁移

@File    :   b2b.py
@Time    :   2021/06/15 20:21:11
@Author  :   SINC
"""


def main():
    bgm_token = auth_bgm(Config.CLIENT_ID, Config.CLIENT_SECRET)

    verify = Verify(Config.SESSDATA, Config.CSRF)

    bgmtran = BangumiTransfer(Config.UID, verify, bgm_token)
    bgmtran.main()


if __name__ == '__main__':
    main()
