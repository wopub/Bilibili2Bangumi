from asyncio import sleep, gather
from collections import deque
from enum import Enum
from types import SimpleNamespace

from aiohttp import ClientError

from config import (
    PARSE_EPISODE_PROGRESS, SKIP_COLLECTED, READ_ONLY
)
from utilities import (
    loop, client, print_debug, print_status,
    try_get_json, try_post_json
)
from episode_progress import parse_episode_progress


class BgmCollectionType(Enum):
    '''Bangumi 条目收藏类型'''
    想看 = 1
    看过 = 2
    在看 = 3
    搁置 = 4
    抛弃 = 5

async def bgm_fetch_subject_collection(data: SimpleNamespace, bgm_id: int):
    '''获取 Bangumi 单个条目当前收藏类型'''
    collection_status = await try_get_json(  # 尝试三次
        3, client,
        f'https://api.bgm.tv/collection/{bgm_id}',
        headers={'Authorization': data.bgm_auth_data}
    )
    if 'status' in collection_status:
        return collection_status['status']['type']
    else:
        return None


async def bgm_update(
    data: SimpleNamespace,
    bgm_id: int, status: str, progress: str
):
    '''更新 Bangumi 单个条目'''
    print_debug(f'开始更新 @ {bgm_id} -> {status} ...')
    do_update = True  # 是否更新该条目
    eps_count = None
    if SKIP_COLLECTED:
        status_previous = await bgm_fetch_subject_collection_status(data, bgm_id)
        if status_previous == status:
            do_update = False
        if PARSE_EPISODE_PROGRESS and status == 'do':
            eps_count = parse_episode_progress(progress)
            if eps_count is not None:
                do_update = True
    if do_update:
        update_watched_eps_flag = False
        # 更新在看分集进度
        if PARSE_EPISODE_PROGRESS and status == 'do' and eps_count is not None:
            update_watched_eps_flag = True
        elif status == 'collect':  # 更新看过分集进度
            # 获取分集总数
            subject_data = await try_get_json(  # 尝试三次
                3, client,
                f'https://api.bgm.tv/subject/{bgm_id}',
                headers={'Authorization': data.bgm_auth_data}
            )
            eps_count = subject_data['eps_count']
            update_watched_eps_flag = True

        if update_watched_eps_flag:
            # 为更新分集进度预先更新收藏为在看
            if (status_previous != 'do'):
                print_debug(f'预先更新收藏 @ {bgm_id} -> do ...')
                if not READ_ONLY:
                    result = await try_post_json(  # 尝试三次
                        3, client,
                        f'https://api.bgm.tv/collection/{bgm_id}/update',
                        data={'status': 'do'},
                        headers={'Authorization': data.bgm_auth_data}
                    )
                    print_debug(f'预先更新收藏完成 @ {bgm_id}')
            if status == 'do':
                print_debug(f'更新在看分集进度 @ {bgm_id} -> {eps_count} ...')
                if not READ_ONLY:
                    ep_info = await try_get_json(  # 尝试三次
                        3, client,
                        f'https://api.bgm.tv/subject/{bgm_id}/ep',
                        headers={'Authorization': data.bgm_auth_data}
                    )
                    ep_id_raw = dict(map(
                        lambda ep: (ep['sort'], str(ep['id'])),
                        filter(lambda ep: ep['type'] == 0, ep_info['eps'])
                    ))
                    ep_watched_info = await try_get_json(  # 尝试三次
                        3, client,
                        f'https://api.bgm.tv/user/'
                        f'{data.bgm_user_id}/progress?subject_id={bgm_id}',
                        headers={'Authorization': data.bgm_auth_data}
                    )
                    if ep_watched_info is None:
                        ep_watched = set()
                    else:
                        ep_watched = set(map(
                            lambda ep: str(ep['id']),
                            filter(
                                lambda ep: ep['status']['id'] == 2,
                                ep_watched_info['eps']
                            )
                        ))
                    ep_ids = deque()
                    for i in range(1, eps_count + 1):
                        if i in ep_id_raw:
                            ep_id = ep_id_raw[i]
                            if ep_id not in ep_watched:
                                ep_ids.append(ep_id)
                    if len(ep_ids) > 0:
                        result = await try_post_json(  # 尝试三次
                            3, client,
                            f'https://api.bgm.tv'
                            f'/ep/{ep_ids[-1]}/status/watched',
                            data={
                                'ep_id': ','.join(ep_ids)
                            },
                            headers={'Authorization': data.bgm_auth_data}
                        )
                        code = result['code']
                        msg = result['error']
                        print_debug(
                            f'更新在看分集进度返回状态 {code} {msg} @ {bgm_id}'
                        )
                        if code > 400:  # 忽略重复更新时的 400 Bad Request
                            print_status(
                                f'** 更新在看分集进度返回状态'
                                f' {code} {msg} @ {bgm_id}'
                            )
                            data.bangumi_failed_count += 1
                            data.bangumi_processed_count += 1
                            return
            elif status == 'collect':
                print_debug(f'更新看过分集进度 @ {bgm_id} -> {eps_count} ...')
                if not READ_ONLY:
                    result = await try_post_json(  # 尝试三次
                        3, client,
                        f'https://api.bgm.tv'
                        f'/subject/{bgm_id}/update/watched_eps',
                        data={'watched_eps': eps_count},
                        headers={'Authorization': data.bgm_auth_data}
                    )
                    code = result['code']
                    msg = result['error']
                    print_debug(
                        f'更新看过分集进度返回状态 {code} {msg} @ {bgm_id}'
                    )
                    if code > 400:  # 忽略重复更新时的 400 Bad Request
                        print_status(
                            f'** 更新看过分集进度返回状态'
                            f' {code} {msg} @ {bgm_id}'
                        )
                        data.bangumi_failed_count += 1
                        data.bangumi_processed_count += 1
                        return

        if (not SKIP_COLLECTED) or status_previous != status:
            print_debug(f'更新收藏 @ {bgm_id} -> {status} ...')
            if not READ_ONLY:
                result = await try_post_json(  # 尝试三次
                    3, client,
                    f'https://api.bgm.tv/collection/{bgm_id}/update',
                    data={'status': status},
                    headers={'Authorization': data.bgm_auth_data}
                )
                print_debug(f'更新收藏完成 @ {bgm_id}')
    else:
        print_debug(f'跳过 @ {bgm_id} -> {status} ...')
    data.bangumi_processed_count += 1
    print_debug(f'完成 @ {bgm_id}！')


async def bgm_update_collection_status():
    '''更新 Bangumi 单个条目收藏状态'''
    pass


async def bgm_update_episode_progress():
    '''更新 Bangumi 单个条目收视进度（点格子）'''
    pass


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
                    loop.create_task(update_one_bgm_data(
                        data,
                        data.bili2bgm_map[bangumi[0]][0],
                        {1: 'wish', 2: 'do', 3: 'collect'}[bangumi[1]],
                        bangumi[2]
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
        await sleep(0.01)
    await check_and_update_bgm_data(data)

    print_debug('等待更新单个 Bangumi 数据任务...')
    await gather(*data.update_one_bgm_data_tasks)

    print_debug('完成！')
