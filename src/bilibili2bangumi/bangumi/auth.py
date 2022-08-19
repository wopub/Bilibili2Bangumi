import asyncio
import webbrowser
import socket

from aiohttp import web

from bilibili2bangumi.utilities import print_debug, client, print_status, try_post_json


_BILIBILI2BANGUMI_APP_ID = 'bgm240762ff550f55c1f'
_BILIBILI2BANGUMI_APP_SECRET = '2393b274af22e86bdd38e06723a69de8'


async def auth_bgm(app_id: str = _BILIBILI2BANGUMI_APP_ID,
                   app_secret: str = _BILIBILI2BANGUMI_APP_SECRET):
    '''取得 Bangumi 授权。
    默认的 App ID 和 App Secret 只用于 Bilibili2Bangumi。
    如果想要在其他地方使用这段代码，请使用自己的 App ID 和 App Secret，并遵守 AGPL-3.0-only。'''
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
    runner = web.ServerRunner(web.Server(handler))
    await runner.setup()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))
    site = web.SockSite(runner, sock)
    await site.start()
    redirect_uri = site.name

    print_debug('打开 Bangumi 授权页面...')
    link = (
        f'https://bgm.tv/oauth/authorize?'
        f'client_id={app_id}&response_type=code&redirect_uri={redirect_uri}'
    )
    webbrowser.open(link)
    print_status('请在弹出的授权页面中点击授权。')
    print_status('若授权页面没有自动弹出，请手动复制链接至浏览器中打开：')
    print_status(f'{link}')

    print_debug('等待 Bangumi 授权请求...')
    while code is None:
        await asyncio.sleep(0.1)
    await site.stop()
    await runner.cleanup()

    print_status('正在尝试取得授权...')

    print_debug('请求 Bangumi 授权码...')
    bgm_auth_data_raw = await try_post_json(  # 尝试五次
        5, client,
        'https://bgm.tv/oauth/access_token',
        data={
            'grant_type': 'authorization_code',
            'client_id': app_id,
            'client_secret': app_secret,
            'code': code,
            'redirect_uri': redirect_uri
        }
    )
    token = (
        f'{bgm_auth_data_raw["token_type"]}'
        f' {bgm_auth_data_raw["access_token"]}'
    )
    print_debug(f'token = "{token}"')
    print_debug('完成！')
    return token, bgm_auth_data_raw['user_id']
