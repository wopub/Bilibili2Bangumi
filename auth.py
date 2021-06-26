from webbrowser import open as webbrowser_open
from asyncio import sleep

from aiohttp import web
from bilibili_api import Credential

from utilities import print_debug, client, print_status, try_for_times_async_json


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
        print_debug('未指定 Bilibili 授权设置！')
        credential = Credential()
    print_debug('完成！')
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

    print_debug('创建 Bangumi 授权请求处理器...')
    app = web.Application()
    app.add_routes([web.get('/', handler)])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 3000)
    await site.start()

    print_debug('打开 Bangumi 授权页面...')
    link = (
        f'https://bgm.tv/oauth/authorize?client_id={app_id}&response_type=code'
    )
    webbrowser_open(link)

    print_status('请在弹出的授权页面中点击授权。')
    print_status('若授权页面没有自动弹出，请手动复制链接至浏览器中打开：')
    print_status(f'{link}')

    print_debug('等待 Bangumi 授权请求...')
    while code is None:
        await sleep(0.001)
    await site.stop()
    await runner.shutdown()

    print_status('正在尝试取得授权...')

    print_debug('请求 Bangumi 授权码...')
    bgm_auth_data_raw = await try_for_times_async_json(  # 尝试五次
        5,
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
    print_debug('完成！')
    return token
