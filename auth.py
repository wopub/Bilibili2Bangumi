from webbrowser import open as webbrowser_open
from asyncio import sleep
from urllib.parse import urlparse, parse_qs

from aiohttp import web
from bilibili_api import Credential


from utilities import print_status, client, try_for_times_async_json


async def auth_bili(sessdata, bili_jct, buvid3):
    '''取得 Bilibili 授权'''
    if (
        sessdata != '你的 Bilibili SESSDATA'
        and bili_jct != '你的 Bilibili bili_jct'
        and buvid3 != '你的 Bilibili buvid3'
    ):
        credential = Credential(
            sessdata=sessdata, bili_jct=bili_jct, buvid3=buvid3
        )
    else:
        print_status('未指定 Bilibili 授权！')
        credential = Credential()
    print_status('完成！')
    return credential


async def auth_bgm(app_id, app_secret):
    '''取得 Bangumi 授权'''

    code = None

    async def handler(request):
        '''Bangumi 授权请求处理器'''
        nonlocal code
        code = request.query['code']
        return web.Response(
            content_type='text/html',
            text='<!DOCTYPE html><html><body><h1 align="center">'
            'Bangumi 授权请求已接受，请关闭此页面。'
            '</h1></body></html>'
        )
    
    print_status('创建 Bangumi 授权请求处理器...')
    app = web.Application()
    app.add_routes([web.get('/', handler)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 3000)
    await site.start()

    print_status('打开 Bangumi 授权页面...')
    webbrowser_open(
        f'https://bgm.tv/oauth/authorize?client_id={app_id}&response_type=code'
    )

    print_status('等待 Bangumi 授权请求...')
    while code is None:
        await sleep(0)
    await site.stop()
    await runner.shutdown()

    print_status('请求 Bangumi 授权码...')
    bgm_auth_data_raw = await try_for_times_async_json(  # 尝试三次
        3,
        lambda: client.post(
            'https://bgm.tv/oauth/access_token',
            data={
                'grant_type': 'authorization_code',
                'client_id': app_id,
                'client_secret': app_secret,
                'code': code,
                'redirect_uri': 'http://localhost:3000'
            }
        )
    )
    token = (
        f'{bgm_auth_data_raw["token_type"]}'
        f' {bgm_auth_data_raw["access_token"]}'
    )
    print_status('完成！')
    return token
