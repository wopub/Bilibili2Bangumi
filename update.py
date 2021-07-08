from asyncio import get_event_loop, sleep, gather
from collections import deque
from types import SimpleNamespace
from math import ceil
from webbrowser import open as webbrowser_open

from aiohttp import ClientError
from bilibili_api.user import User, BangumiType
from bilibili_api.bangumi import get_meta
from bilibili_api.exceptions import ResponseCodeException

from config import READ_ONLY, OPEN_FAILED_BANGUMI_BILI_PAGE
from utilities import (
    client, print_debug, print_status,
    try_for_times_async_chain, try_for_times_async_json
)


async def get_one_bili_data(data: SimpleNamespace, page: int):
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
            bangumi['media_id'], bangumi['follow_status']
        ),
        bangumi_data['list']
    ))
    data.bili_processed_count += 1
    if page == 1:
        return ceil(bangumi_data['total'] / 15)  # 计算并返回总页数


async def get_bili_data(data: SimpleNamespace):
    '''获取 Bilibili 追番数据'''
    print_debug('获取第一页 Bilibili 追番数据...')
    try:
        data.bili_total_count = await get_one_bili_data(data, 1)
    except ResponseCodeException:
        print_status(
            '** Bilibili 授权设置不正确，无法读取隐私设置'
            '未公开的 Bilibili 追番数据！'
        )
        exit(1)

    print_debug('创建并等待获取单个 Bilibili 追番数据任务...')
    await gather(*(
        data.loop.create_task(get_one_bili_data(data, page))
        for page in range(2, data.bili_total_count + 1)
    ))
    print_debug('完成！')


async def update_one_bgm_data(
    data: SimpleNamespace,
    bgm_id: int, status: str
):
    '''更新单个 Bangumi 动画数据'''
    if status == 'collect':  # 看过 -> 更新分集进度
        # 获取分集总数
        subject_data = await try_for_times_async_json(  # 尝试三次
            3,
            lambda: client.get(
                f'https://api.bgm.tv/subject/{bgm_id}',
                headers={'Authorization': data.bgm_auth_data}
            )
        )
        eps_count = subject_data['eps_count']
        print_debug(f'更新分集进度 @ {bgm_id} -> {eps_count} ...')
        if not READ_ONLY:
            response = await try_for_times_async_chain(  # 尝试三次
                3,
                lambda: client.post(
                    f'https://api.bgm.tv'
                    f'/subject/{bgm_id}/update/watched_eps',
                    data={'watched_eps': eps_count},
                    headers={'Authorization': data.bgm_auth_data}
                )
            )
            response.raise_for_status()
    print_debug(f'更新收藏 @ {bgm_id} -> {status} ...')
    if not READ_ONLY:
        response = await try_for_times_async_chain(  # 尝试三次
            3,
            lambda: client.post(
                f'https://api.bgm.tv/collection/{bgm_id}/update',
                data={'status': status},
                headers={'Authorization': data.bgm_auth_data}
            )
        )
        response.raise_for_status()
    data.bangumi_processed_count += 1
    print_debug(f'完成 @ {bgm_id}！')


async def check_and_update_bgm_data(data: SimpleNamespace):
    '''检查剩余数据并更新 Bangumi 动画数据'''
    while len(data.bangumi_remaining) > 0:
        bangumi = data.bangumi_remaining.popleft()
        if (
            bangumi[0] in data.bili2bgm_map
            and data.bili2bgm_map[bangumi[0]][0] is not None
        ):
            try:
                data.update_one_bgm_data_tasks.append(
                    data.loop.create_task(update_one_bgm_data(
                        data,
                        data.bili2bgm_map[bangumi[0]][0],
                        {1: 'wish', 2: 'do', 3: 'collect'}[bangumi[1]]
                    ))
                )
            except ClientError:
                pass
            else:
                continue
        data.bangumi_failed.append(bangumi[0])
        data.bangumi_failed_count += 1
        data.bangumi_processed_count += 1


async def update_bgm_data(data: SimpleNamespace):
    '''更新 Bangumi 动画数据'''
    print_debug('创建更新单个 Bangumi 数据任务...')
    while not data.get_bili_data_task.done():
        await check_and_update_bgm_data(data)
        await sleep(0.001)
    await check_and_update_bgm_data(data)

    print_debug('等待更新单个 Bangumi 数据任务...')
    await gather(*data.update_one_bgm_data_tasks)

    print_debug('完成！')


async def print_unknown(data: SimpleNamespace, bangumi: int):
    '''打印没有对应的数据的 Bilibili 追番数据'''
    bangumi_meta = await get_meta(bangumi, data.bili_auth_data)
    print_status(
        f'** {bangumi_meta["media"]["title"]}'
        f'（Bilibili 编号 md{bangumi}）没有对应的数据！'
    )


async def print_progress(data: SimpleNamespace):
    '''打印进度'''
    while len(data.bangumi_failed) > 0:
        bangumi = data.bangumi_failed.popleft()
        if bangumi in data.bili2bgm_map:
            if data.bili2bgm_map[bangumi][0] is not None:
                print_status(
                    f'** {data.bili2bgm_map[bangumi][1]}'
                    f'（Bilibili 编号 md{bangumi}，'
                    f'Bangumi 编号 {data.bili2bgm_map[bangumi][0]}）更新失败！'
                )
            else:
                print_status(
                    f'** {data.bili2bgm_map[bangumi][1]}'
                    f'（Bilibili 编号 md{bangumi}）'
                    f'没有对应的 Bangumi 数据！'
                )
        else:
            data.print_unknown_tasks.append(
                data.loop.create_task(
                    print_unknown(data, bangumi)
                )
            )
        if OPEN_FAILED_BANGUMI_BILI_PAGE:
            webbrowser_open(
                f'https://www.bilibili.com/bangumi/media/md{bangumi}/'
            )

    bili_status = '[Bilibili %d/%d %.1f%%]' % (
        data.bili_processed_count,
        data.bili_total_count,
        (data.bili_processed_count) / data.bili_total_count * 100
    )
    bgm_status = '[Bangumi %d/%d %.1f%% (失败 %s)]' % (
        data.bangumi_processed_count,
        data.bangumi_total,
        data.bangumi_processed_count / data.bangumi_total * 100,
        data.bangumi_failed_count
    )
    print_status(
        f'{bili_status} -> {bgm_status} {"." * data.animation_points}',
        end='\r'
    )
    data.animation_points += 1
    if data.animation_points > 3:
        data.animation_points = 1


async def get_and_update(bili2bgm_map, bili_auth_data, bili_uid, bgm_auth_data):
    '''获取 Bilibili 番剧数据并更新 Bangumi 动画数据'''
    data = SimpleNamespace(
        bili2bgm_map=bili2bgm_map,
        user=User(bili_uid, bili_auth_data),
        bili_auth_data=bili_auth_data,
        bgm_auth_data=bgm_auth_data,
        bili_processed_count=0,
        bili_total_count=None,
        bangumi_total=0,
        # [(bili media id, 1: 想看 | 2: 在看 | 3: 看过), ...]
        bangumi_remaining=deque(),
        bangumi_processed_count=0,
        bangumi_failed=deque(),
        bangumi_failed_count=0,
        animation_points=1,
        get_bili_data_task=None,
        update_bgm_data_task=None,
        update_one_bgm_data_tasks=deque(),
        print_unknown_tasks=deque(),
        loop=get_event_loop()
    )

    print_debug('创建获取 Bilibili 数据任务 -> [get_bili_data]')
    data.get_bili_data_task = data.loop.create_task(get_bili_data(data))

    print_debug('创建更新 Bangumi 数据任务 -> [update_bgm_data]')
    data.update_bgm_data_task = data.loop.create_task(update_bgm_data(data))

    print_debug('等待任务...')

    while data.bili_total_count is None:
        await sleep(0.001)

    while not (
        data.get_bili_data_task.done()
        and data.update_bgm_data_task.done()
    ):
        await print_progress(data)
        await sleep(0.1)

    await data.get_bili_data_task
    await data.update_bgm_data_task

    await print_progress(data)
    await gather(*data.print_unknown_tasks)
    await print_progress(data)

    print()
