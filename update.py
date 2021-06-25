from asyncio import get_event_loop, sleep
from collections import deque
from math import ceil
from webbrowser import open as webbrowser_open

from aiohttp import ClientError
from bilibili_api.user import User, BangumiType

from config import OPEN_FAILED_BANGUMI_BILI_PAGE
from utilities import (
    client, print_status,
    try_for_times_async_chain, try_for_times_async_json
)


async def get_and_update(bili2bgm_map, bili_auth_data, bili_uid, bgm_auth_data):
    '''获取 Bilibili 番剧数据并更新 Bangumi 动画数据'''
    bili_processed_count = 0
    bili_total_count = None
    bangumi_total = 0
    # [(bili media id, 1: 想看 | 2: 在看 | 3: 看过), ...]
    bangumi_remaining = deque()
    bangumi_processed_count = 0
    bangumi_failed = deque()
    bangumi_failed_count = 0
    loop = get_event_loop()

    async def get_bili_data(auth_data, uid):
        '''获取 Bilibili 番剧数据'''
        nonlocal bili_processed_count, bili_total_count
        nonlocal bangumi_total, bangumi_remaining, loop

        async def get_one_bili_data(user, page):
            '''获取单个 Bilibili 番剧数据'''
            nonlocal bili_processed_count, bili_total_count
            nonlocal bangumi_total, bangumi_remaining
            bangumi_data = await try_for_times_async_chain(  # 尝试三次
                3,
                lambda: user.get_subscribed_bangumis(
                    page,
                    BangumiType.BANGUMI
                )
            )
            bangumi_total += len(bangumi_data['list'])
            bangumi_remaining.extend(map(
                lambda bangumi: (
                    bangumi['media_id'], bangumi['follow_status']
                ),
                bangumi_data['list']
            ))
            bili_processed_count += 1
            if page == 1:
                return ceil(bangumi_data['total'] / 15)  # 计算并返回总页数

        user = User(uid, auth_data)
        print_status('获取第一页 Bilibili 番剧数据...')
        bili_total_count = await get_one_bili_data(user, 1)

        print_status('创建并等待获取单个 Bilibili 数据任务...')
        for task in [
            loop.create_task(get_one_bili_data(user, page))
            for page in range(2, bili_total_count + 1)
        ]:
            await task

        print_status('完成！')

    print_status('创建获取 Bilibili 数据任务 -> [get_bili_data]')
    get_bili_data_task = loop.create_task(get_bili_data(
        bili_auth_data, bili_uid
    ))

    async def update_bgm_data(auth_data):
        '''更新 Bangumi 动画数据'''
        nonlocal bangumi_remaining, bangumi_processed_count
        nonlocal bangumi_failed, bangumi_failed_count
        nonlocal get_bili_data_task, loop

        async def update_one_bgm_data(auth_data, bgm_id, status):
            '''更新单个 Bangumi 动画数据'''
            nonlocal bangumi_processed_count
            if status == 'collect':  # 看过 -> 更新分集进度
                # 获取分集总数
                subject_data = await try_for_times_async_json(  # 尝试三次
                    3,
                    lambda: client.get(
                        f'https://api.bgm.tv/subject/{bgm_id}',
                        headers={'Authorization': auth_data}
                    )
                )
                eps_count = subject_data['eps_count']
                # 更新分集进度
                response = await try_for_times_async_chain(  # 尝试三次
                    3,
                    lambda: client.post(
                        f'https://api.bgm.tv'
                        f'/subject/{bgm_id}/update/watched_eps',
                        data={'watched_eps': eps_count},
                        headers={'Authorization': auth_data}
                    )
                )
                response.raise_for_status()
            # 更新收藏
            response = await try_for_times_async_chain(  # 尝试三次
                3,
                lambda: client.post(
                    f'https://api.bgm.tv/collection/{bgm_id}/update',
                    data={'status': status},
                    headers={'Authorization': auth_data}
                )
            )
            response.raise_for_status()
            bangumi_processed_count += 1

        update_one_bgm_data_tasks = deque()

        async def check_and_update_bgm_data(auth_data):
            '''检查剩余数据并更新 Bangumi 动画数据'''
            nonlocal bangumi_remaining, bangumi_processed_count
            nonlocal bangumi_failed, bangumi_failed_count
            nonlocal update_one_bgm_data_tasks, loop
            while len(bangumi_remaining) > 0:
                bangumi = bangumi_remaining.popleft()
                if bangumi[0] in bili2bgm_map:
                    try:
                        update_one_bgm_data_tasks.append(
                            loop.create_task(update_one_bgm_data(
                                auth_data,
                                bili2bgm_map[bangumi[0]],
                                {1: 'wish', 2: 'do', 3: 'collect'}[bangumi[1]]
                            ))
                        )
                    except ClientError:
                        pass
                    else:
                        continue
                bangumi_failed.append(bangumi[0])
                bangumi_failed_count += 1
                bangumi_processed_count += 1

        print_status('创建更新单个 Bangumi 数据任务...')
        while not get_bili_data_task.done():
            await check_and_update_bgm_data(auth_data)
            await sleep(0.001)
        await check_and_update_bgm_data(auth_data)

        print_status('等待更新单个 Bangumi 数据任务...')
        for task in update_one_bgm_data_tasks:
            await task

        print_status('完成！')

    print_status('创建更新 Bangumi 数据任务 -> [update_bgm_data]')
    update_bgm_data_task = loop.create_task(update_bgm_data(bgm_auth_data))

    print_status('等待任务...')
    print_status('[Bilibili 0/?]', end='\r')
    while bili_total_count is None:
        await sleep(0.001)

    animation_points = 1

    async def print_progress():
        nonlocal animation_points
        while len(bangumi_failed) > 0:
            bangumi = bangumi_failed.popleft()
            if bangumi in bili2bgm_map:
                print_status(
                    f'** Bilibili 编号 md{bangumi}，'
                    f'Bangumi 编号 {bili2bgm_map[bangumi]} 更新失败！',
                    2
                )
            else:
                print_status(
                    f'** Bilibili 编号 md{bangumi}'
                    f' 没有对应的 Bangumi 数据！',
                    2
                )
            if OPEN_FAILED_BANGUMI_BILI_PAGE:
                webbrowser_open(
                    f'https://www.bilibili.com/bangumi/media/md{bangumi}/'
                )

        bili_status = '[Bilibili %d/%d %.1f%%]' % (
            bili_processed_count,
            bili_total_count,
            (bili_processed_count) / bili_total_count * 100
        )
        bgm_status = '[Bangumi %d/%d %.1f%% (失败 %s)]' % (
            bangumi_processed_count,
            bangumi_total,
            bangumi_processed_count / bangumi_total * 100,
            bangumi_failed_count
        )
        print_status(
            f'{bili_status} -> {bgm_status} {"." * animation_points}',
            2,
            end='\r'
        )
        animation_points += 1
        if animation_points > 3:
            animation_points = 1

    while not (
        get_bili_data_task.done()
        and update_bgm_data_task.done()
    ):
        await print_progress()
        await sleep(0.1)
    await print_progress()
    print()
