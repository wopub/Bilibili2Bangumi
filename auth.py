from json.decoder import JSONDecodeError
from webbrowser import open as webbrowser_open
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from httpx import post, RequestError
from bilibili_api import Credential


from utilities import try_for_times


def auth_bili(sessdata, bili_jct, buvid3):
    '''取得 Bilibili 授权'''
    if (
        sessdata != "你的 SESSDATA"
        and bili_jct != "你的 bili_jct"
        and buvid3 != "你的 buvid3"
    ):
        return Credential(
            sessdata=sessdata, bili_jct=bili_jct, buvid3=buvid3
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
            }
        ).json(),
        (RequestError, JSONDecodeError)
    )
    return (
        f'{bgm_auth_data_raw["token_type"]} {bgm_auth_data_raw["access_token"]}'
    )
