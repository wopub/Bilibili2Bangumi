from asyncio import get_event_loop, sleep
from bili2bangumi import update_bgm_one_bangumi_data
from collections import defaultdict, deque
from typing import Callable, Union, Tuple
from webbrowser import open as webbrowser_open
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from httpx import get, post, AsyncClient, RequestError
from bilibili_api.utils import Credential


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


def try_for_times(
    times: int,
    func: Callable,
    exception: Union[Exception, Tuple[Exception]]
):
    '''尝试多次'''
    while True:
        times -= 1
        try:
            return func()
        except exception:
            if times == 0:
                raise
            continue


def get_bili2bgm_map(bangumi_data_link):
    '''构造 Bilibili -> Bangumi 动画编号映射'''
    print('  请求动画数据...')
    bangumi_data = try_for_times(  # 尝试三次
        3,
        lambda: get(bangumi_data_link).json(),
        RequestError
    )
    print('  构造 Bilibili -> Bangumi 动画编号映射...')
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


def auth_bgm(address, app_id, app_secret):
    '''取得 Bangumi 授权'''

    class BgmAuthHTTPRequestHandler(BaseHTTPRequestHandler):
        '''Bangumi 授权请求处理器'''

        def do_GET(self):
            self.server.code = parse_qs(urlparse(self.path).query)['code'][0]

    print('  创建 Bangumi 授权请求处理器...')
    server = HTTPServer(address, BgmAuthHTTPRequestHandler)
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
    return f'{bgm_auth_data_raw["token_type"]} {bgm_auth_data_raw["access_token"]}'


async def get_bili_bangumi_data(auth_data, uid, bili2bgm_map, bangumi_remaining):
    '''获取 Bilibili 番剧数据'''


async def update_bgm_bangumi_data(auth_data, bangumi_remaining):
    '''更新 Bangumi 动画数据'''


async def get_and_update(bili2bgm_map, bili_auth_data, bili_uid, bgm_auth_data):
    '''获取 Bilibili 番剧数据并更新 Bangumi 动画数据'''
    loop = get_event_loop()
    bangumi_remaining = deque()
    print('  创建获取 Bilibili 番剧数据任务...')
    get_bili_bangumi_data_task = loop.create_task(get_bili_bangumi_data(
        bili_auth_data, bili_uid, bili2bgm_map, bangumi_remaining
    ))
    print('  创建更新 Bangumi 动画数据任务...')
    update_bgm_bangumi_data_task = loop.create_task(update_bgm_bangumi_data(
        bgm_auth_data, bangumi_remaining
    ))
    print('  等待任务完成...')
    while not (
        get_bili_bangumi_data_task.done
        and update_bgm_bangumi_data_task.done
    ):
        await sleep(0.2)


def main():
    BANGUMI_DATA_LINK = \
        'https://cdn.jsdelivr.net/npm/bangumi-data@0.3/dist/data.json'
    print('构造 Bilibili -> Bangumi 番剧编号映射...')
    bili2bgm_map = get_bili2bgm_map(BANGUMI_DATA_LINK)
    print('取得 Bilibili 授权...')
    bili_auth_data = auth_bili(SESSDATA, BILI_JCT, BUVID3)
    print('取得 Bangumi 授权...')
    bgm_auth_data = auth_bgm(('localhost', 3000), APP_ID, APP_SECRET)
    print('获取 Bilibili 番剧数据并更新 Bangumi 动画数据...')
    get_event_loop().run_until_complete(
        get_and_update(bili2bgm_map, bili_auth_data, BILI_UID, bgm_auth_data)
    )


if __name__ == '__main__':
    main()
