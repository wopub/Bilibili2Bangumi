from asyncio import get_event_loop
from collections import deque
from typing import Callable, Coroutine, Union, Tuple
from webbrowser import open as webbrowser_open
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from math import ceil
from traceback import format_exception_only

from httpx import get, post, AsyncClient, RequestError, HTTPStatusError
from bilibili_api import Credential
from bilibili_api.user import User, BangumiType
from aiohttp import ClientError


####################  设置  ####################

# 基础设置，必填
BILI_UID = '你的 Bilibili UID'

# bilibili_api 授权设置，选填（隐私设置为不公开则必填）
SESSDATA = '你的 Bilibili SESSDATA'
BILI_JCT = '你的 Bilibili bili_jct'
BUVID3 = '你的 Bilibili buvid3'

# Bangumi OAuth2 授权设置，必填
APP_ID = '你的 Bangumi App ID'
APP_SECRET = '你的 Bangumi App Secret'

####################  设置  ####################


def print_exception(e: Exception, tried_times: int, times: int) -> bool:
    '''异常被引发时打印异常并判断是否退出（True：继续，False：退出）'''
    print('** 异常被引发！')
    print(format_exception_only(type(e), e)[-1])
    if tried_times == times:
        print(f'** {tried_times} 次尝试均失败，退出！')
        return False
    print(f'** 第 {tried_times} 次尝试失败！')
    tried_times += 1
    print(f'** 进行第 {tried_times} 次尝试...')
    return True


def try_for_times(
    times: int,
    func: Callable,
    exception: Union[Exception, Tuple[Exception]]
):
    '''尝试多次'''
    tried_times = 1
    while True:
        try:
            return func()
        except exception as e:
            if print_exception(e, tried_times, times):
                continue
            else:
                raise


async def try_for_times_async(
    times: int,
    func: Callable[[], Coroutine],
    exception: Union[Exception, Tuple[Exception]]
):
    '''尝试多次（异步）'''
    tried_times = 1
    while True:
        try:
            return await func()
        except exception as e:
            if print_exception(e, tried_times, times):
                continue
            else:
                raise


def get_bili2bgm_map(bangumi_data_link):
    '''构造 Bilibili 编号（media） -> Bangumi 编号映射'''
    BANGUMI_DATA_LINK = \
        'https://cdn.jsdelivr.net/npm/bangumi-data@0.3/dist/data.json'
    print('  请求动画数据...')
    bangumi_data = try_for_times(  # 尝试三次
        3,
        lambda: get(bangumi_data_link).json(),
        RequestError
    )
    print('  构造编号映射...')
    bili2bgm_map = {}
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
    return bili2bgm_map, bangumi_data


def auth_bili(sessdata, bili_jct, buvid3):
    '''取得 Bilibili 授权'''
    if (
        sessdata != "你的 SESSDATA"
        and bili_jct != "你的 bili_jct"
        and buvid3 != "你的 buvid3"
    ):
        return Credential(
            sessdata=SESSDATA, bili_jct=BILI_JCT, buvid3=BUVID3
        )
    else:
        print('  未指定 Bilibili 授权！')
        return Credential()


def auth_bgm(app_id, app_secret):
    '''取得 Bangumi 授权'''

    class BgmAuthHTTPRequestHandler(BaseHTTPRequestHandler):
        '''Bangumi 授权请求处理器'''

        def do_GET(self):
            self.server.code = parse_qs(urlparse(self.path).query)['code'][0]

    print('  创建 Bangumi 授权请求处理器...')
    server = HTTPServer(('localhost', 3000), BgmAuthHTTPRequestHandler)
    print('  打开 Bangumi 授权页面...')
    webbrowser_open(
        f'https://bgm.tv/oauth/authorize?client_id={app_id}&response_type=code'
    )
    print('  等待 Bangumi 授权请求...')
    server.handle_request()
    print('  请求 Bangumi 授权码...')
    bgm_auth_data_raw = try_for_times(  # 尝试三次
        3,
        lambda: post(
            'https://bgm.tv/oauth/access_token',
            data={
                'grant_type': 'authorization_code',
                'client_id': app_id,
                'client_secret': app_secret,
                'code': server.code,
                'redirect_uri': 'http://localhost:3000'
            },
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64;'
                ' rv:89.0) Gecko/20100101 Firefox/89.0'
            }
        ).json(),
        RequestError
    )
    return (
        f'{bgm_auth_data_raw["token_type"]} {bgm_auth_data_raw["access_token"]}'
    )


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
            bangumi_remaining.extend(map(
                lambda bangumi: (
                    bangumi['media_id'], bangumi['follow_status']
                ),
                bangumi_data['list']
            ))

    loop = get_event_loop()
    print('  创建获取 Bilibili 番剧数据任务...')
    get_bili_bangumi_data_task = loop.create_task(get_bili_bangumi_data(
        bili_auth_data, bili_uid, bili2bgm_map
    ))

    async def update_one_bgm_bangumi_data(client, auth_data, bgm_id, status):
        '''更新一部 Bangumi 动画数据'''
        if status == 'collect':  # 看过 -> 更新分集进度
            # 获取分集总数
            subject_data = await try_for_times_async(  # 尝试三次
                3,
                lambda: client.get(
                    f'https://api.bgm.tv/subject/{bgm_id}',
                    headers={
                        'User-Agent': 'Mozilla/5.0'
                        ' (Windows NT 10.0; Win64; x64; rv:89.0)'
                        ' Gecko/20100101 Firefox/89.0'
                    }
                ),
                RequestError
            )
            eps_count = subject_data.json()['eps_count']
            # 更新分集进度
            response = await try_for_times_async(  # 尝试三次
                3,
                lambda: client.post(
                    f'https://api.bgm.tv/subject/{bgm_id}/update/{eps_count}',
                    headers={
                        'User-Agent': 'Mozilla/5.0'
                        ' (Windows NT 10.0; Win64; x64; rv:89.0)'
                        ' Gecko/20100101 Firefox/89.0',
                        'Authorization': auth_data
                    }
                ),
                RequestError
            )
            response.raise_for_status()
        # 更新收藏
        response = await try_for_times_async(  # 尝试三次
            3,
            lambda: client.post(
                f'https://api.bgm.tv/collection/{bgm_id}/update',
                data={
                    'status': status
                },
                headers={
                    'User-Agent': 'Mozilla/5.0'
                    ' (Windows NT 10.0; Win64; x64; rv:89.0)'
                    ' Gecko/20100101 Firefox/89.0',
                    'Authorization': auth_data
                }
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
            while not get_bili_bangumi_data_task.done:
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
                yield

    print('  创建更新 Bangumi 动画数据任务...')
    update_bgm_bangumi_data_task = loop.create_task(update_bgm_bangumi_data(
        bgm_auth_data
    ))

    print('  [Bilibili 0/?]', end='\r')
    while bili_pages_total is None:
        yield

    animation_points = 1
    while not (
        get_bili_bangumi_data_task.done
        and update_bgm_bangumi_data_task.done
    ):
        while len(bangumi_failed) > 0:
            bangumi = bangumi_failed.popleft()
            print('%50s' % '一部动画更新失败！')
            print(f'  https://www.bilibili.com/bangumi/media/md{bangumi}/')
            if bangumi in bili2bgm_map:
                print(f'  https://bangumi.tv/subject/{bili2bgm_map[bangumi]}')
            else:
                print('  没有对应的 Bangumi 动画数据！')
        bili_status = '[Bilibili %d/%d %.1f%%]' % (
            bili_page_current - 1,
            bili_pages_total,
            (bili_page_current - 1) / bili_pages_total
        )
        bgm_status = '[Bangumi %d/%d %.1f%% (失败 %s)]' % (
            bangumi_processed,
            bangumi_total,
            bangumi_processed / bangumi_total,
            bangumi_failed_count
        )
        print('%50s' % (
            f'  {bili_status} -> {bgm_status}'
            f' {"." * animation_points}'
        ), end='\r')
        animation_points += 1
        if animation_points > 3:
            animation_points = 1
        yield
    print()


def main():
    print('构造 Bilibili 编号 -> Bangumi 编号映射...')
    bili2bgm_map, bangumi_data_raw = get_bili2bgm_map()
    print('取得 Bilibili 授权...')
    bili_auth_data = auth_bili(SESSDATA, BILI_JCT, BUVID3)
    print('取得 Bangumi 授权...')
    bgm_auth_data = auth_bgm(APP_ID, APP_SECRET)
    print('获取 Bilibili 番剧数据并更新 Bangumi 动画数据...')
    get_event_loop().run_until_complete(
        get_and_update(bili2bgm_map, bili_auth_data, BILI_UID, bgm_auth_data)
    )


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('已取消！')
    else:
        print('完成！')
