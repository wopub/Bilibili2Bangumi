from asyncio import sleep, gather
from collections import deque
from types import SimpleNamespace
from math import ceil
from typing import Tuple
from webbrowser import open as webbrowser_open

from aiohttp import ClientError
from bilibili_api.user import User, BangumiType
from bilibili_api.bangumi import get_meta
from bilibili_api.exceptions import ResponseCodeException

from config import (
    PARSE_EPISODE_PROGRESS, SKIP_COLLECTED, READ_ONLY,
    OPEN_FAILED_BANGUMI_BILI_PAGE
)
from utilities import (
    loop, client, print_debug, print_status,
    try_for_times_async_chain, try_get_json, try_post_json
)
from episode_progress import parse_episode_progress

async def fetch_single_bili_data(data: SimpleNamespace, page: int):
    '''获取单个 Bilibili 追番数据'''
    print_debug(f'获取追番数据 @ {page} ...')
    bangumi_data = await try_for_times_async_chain(  # 尝试三次
        3,
        lambda: data.user.get_subscribed_bangumis(
            page,
            BangumiType.BANGUMI
        )
    )
    data.bangumi_total += len(bangumi_data['list'])
    data.bangumi_remaining.extend(map(
        lambda bangumi: (
            bangumi['media_id'], bangumi['follow_status'], bangumi['progress']
        ),
        bangumi_data['list']
    ))
    data.bili_processed_count += 1
    if page == 1:
        return ceil(bangumi_data['total'] / 15)  # 计算并返回总页数


async def fetch_bili_data(data: SimpleNamespace):
    '''获取 Bilibili 追番数据'''
    print_debug('获取第一页 Bilibili 追番数据...')
    try:
        data.bili_total_count = await fetch_single_bili_data(data, 1)
    except ResponseCodeException:
        print_status(
            '** Bilibili 授权设置不正确，无法读取隐私设置'
            '未公开的 Bilibili 追番数据！'
        )
        exit(1)

    print_debug('创建并等待获取单个 Bilibili 追番数据任务...')
    await gather(*(
        loop.create_task(fetch_single_bili_data(data, page))
        for page in range(2, data.bili_total_count + 1)
    ))
    print_debug('完成！')


async def get_bangumi_title(data: SimpleNamespace, bangumi: int) -> str:
    return (await get_meta(bangumi, data.bili_auth_data))["media"]["title"]


async def print_unknown(data: SimpleNamespace, bangumi: int):
    '''打印没有对应的数据的 Bilibili 追番数据'''
    print_status(
        f'** {get_bangumi_title(data, bangumi)}'
        f'（Bilibili 编号 md{bangumi}）没有对应的数据！'
    )
