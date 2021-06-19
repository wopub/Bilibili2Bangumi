from asyncio import get_event_loop, sleep
from collections import deque
from math import ceil

from httpx import AsyncClient, RequestError, HTTPStatusError
from bilibili_api.user import User, BangumiType
from aiohttp import ClientError


from utilities import try_for_times_async


async def get_and_update(bili2bgm_map, bili_auth_data, bili_uid, bgm_auth_data):
    '''获取 Bilibili 番剧数据并更新 Bangumi 动画数据'''
    bili_page_current = bili_pages_total = None
    bangumi_total = 0
    # [(bili media id, 1: 想看 | 2: 在看 | 3: 看过), ...]
    bangumi_remaining = deque()
    bangumi_processed = 0
    bangumi_failed = deque()
    bangumi_failed_count = 0

    async def get_bili_bangumi_data(credential, uid, bili2bgm_map):
        '''获取 Bilibili 番剧数据'''
        nonlocal bili_page_current, bili_pages_total
        nonlocal bangumi_total, bangumi_remaining
        user = User(uid, credential)
        # 获取第一页
        bangumi_data = await try_for_times_async(  # 尝试三次
            3,
            lambda: user.get_subscribed_bangumis(1, BangumiType.BANGUMI),
            ClientError
        )
        bili_pages_total = ceil(bangumi_data['total'] / 15)
        bangumi_total += len(bangumi_data['list'])
        bangumi_remaining.extend(map(
            lambda bangumi: (
                bangumi['media_id'], bangumi['follow_status']
            ),
            bangumi_data['list']
        ))
        # 获取剩下的页
        for bili_page_current in range(2, bili_pages_total + 1):
            bangumi_data = await try_for_times_async(  # 尝试三次
                3,
                lambda: user.get_subscribed_bangumis(
                    bili_page_current,
                    BangumiType.BANGUMI
                ),
                ClientError
            )
            bangumi_total += len(bangumi_data['list'])
            bangumi_remaining.extend(map(
                lambda bangumi: (
                    bangumi['media_id'], bangumi['follow_status']
                ),
                bangumi_data['list']
            ))
        bili_page_current += 1

    loop = get_event_loop()
    print('  创建获取 Bilibili 番剧数据任务...')
    get_bili_bangumi_data_task = loop.create_task(get_bili_bangumi_data(
        bili_auth_data, bili_uid, bili2bgm_map
    ))

    async def update_one_bgm_bangumi_data(client, auth_data, bgm_id, status):
        '''更新单个 Bangumi 动画数据'''
        if status == 'collect':  # 看过 -> 更新分集进度
            # 获取分集总数
            subject_data = await try_for_times_async(  # 尝试三次
                3,
                lambda: client.get(
                    f'https://api.bgm.tv/subject/{bgm_id}',
                    headers={'Authorization': auth_data}
                ),
                RequestError
            )
            eps_count = subject_data.json()['eps_count']
            # 更新分集进度
            response = await try_for_times_async(  # 尝试三次
                3,
                lambda: client.post(
                    f'https://api.bgm.tv/subject/{bgm_id}/update/{eps_count}',
                    headers={'Authorization': auth_data}
                ),
                RequestError
            )
            response.raise_for_status()
        # 更新收藏
        response = await try_for_times_async(  # 尝试三次
            3,
            lambda: client.post(
                f'https://api.bgm.tv/collection/{bgm_id}/update',
                data={'status': status},
                headers={'Authorization': auth_data}
            ),
            RequestError
        )
        response.raise_for_status()

    async def update_bgm_bangumi_data(auth_data):
        '''更新 Bangumi 动画数据'''
        nonlocal bangumi_remaining, bangumi_processed
        nonlocal bangumi_failed, bangumi_failed_count
        nonlocal get_bili_bangumi_data_task
        async with AsyncClient() as client:
            while not get_bili_bangumi_data_task.done():
                while len(bangumi_remaining) > 0:
                    bangumi = bangumi_remaining.popleft()
                    if bangumi[0] in bili2bgm_map:
                        try:
                            await update_one_bgm_bangumi_data(
                                client,
                                auth_data,
                                bili2bgm_map[bangumi[0]],
                                {1: 'wish', 2: 'do', 3: 'collect'}[bangumi[1]]
                            )
                        except (RequestError, HTTPStatusError):
                            bangumi_failed.append(bangumi[0])
                            bangumi_failed_count += 1
                    else:
                        bangumi_failed.append(bangumi[0])
                        bangumi_failed_count += 1
                    bangumi_processed += 1
                await sleep(0)
            while len(bangumi_remaining) > 0:
                bangumi = bangumi_remaining.popleft()
                if bangumi[0] in bili2bgm_map:
                    try:
                        await update_one_bgm_bangumi_data(
                            client,
                            auth_data,
                            bili2bgm_map[bangumi[0]],
                            {1: 'wish', 2: 'do', 3: 'collect'}[bangumi[1]]
                        )
                    except (RequestError, HTTPStatusError):
                        bangumi_failed.append(bangumi[0])
                        bangumi_failed_count += 1
                else:
                    bangumi_failed.append(bangumi[0])
                    bangumi_failed_count += 1
                bangumi_processed += 1

    print('  创建更新 Bangumi 动画数据任务...')
    update_bgm_bangumi_data_task = loop.create_task(update_bgm_bangumi_data(
        bgm_auth_data
    ))

    print('  [Bilibili 0/?]', end='\r')
    while bili_pages_total is None:
        await sleep(0)

    animation_points = 1
    while not (
        get_bili_bangumi_data_task.done()
        and update_bgm_bangumi_data_task.done()
    ):
        while len(bangumi_failed) > 0:
            bangumi = bangumi_failed.popleft()
            print('%-60s' % '  一部动画更新失败！')
            print(f'    https://www.bilibili.com/bangumi/media/md{bangumi}/')
            if bangumi in bili2bgm_map:
                print(
                    f'    https://bangumi.tv/subject/{bili2bgm_map[bangumi]}')
            else:
                print('    没有对应的 Bangumi 动画数据！')
        bili_status = '[Bilibili %d/%d %.1f%%]' % (
            bili_page_current - 1,
            bili_pages_total,
            (bili_page_current - 1) / bili_pages_total * 100
        )
        bgm_status = '[Bangumi %d/%d %.1f%% (失败 %s)]' % (
            bangumi_processed,
            bangumi_total,
            bangumi_processed / bangumi_total * 100,
            bangumi_failed_count
        )
        print('%-60s' % (
            f'  {bili_status} -> {bgm_status}'
            f' {"." * animation_points}'
        ), end='\r')
        animation_points += 1
        if animation_points > 3:
            animation_points = 1
        await sleep(0)
    bili_status = '[Bilibili %d/%d %.1f%%]' % (
        bili_page_current - 1,
        bili_pages_total,
        (bili_page_current - 1) / bili_pages_total * 100
    )
    bgm_status = '[Bangumi %d/%d %.1f%% (失败 %s)]' % (
        bangumi_processed,
        bangumi_total,
        bangumi_processed / bangumi_total * 100,
        bangumi_failed_count
    )
    print('%-60s' % (
        f'  {bili_status} -> {bgm_status}'
        f' {"." * animation_points}'
    ), end='\r')
    print()
