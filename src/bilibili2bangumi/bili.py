from math import ceil

from bilibili_api import Credential
from bilibili_api.user import User, BangumiType
from bilibili_api.bangumi import Bangumi

from .utilities import print_debug, try_


def auth_bili(sessdata: str, bili_jct: str, buvid3: str) -> Credential:
    '''取得 Bilibili 授权'''
    if (sessdata != '你的 Bilibili SESSDATA'
            and bili_jct != '你的 Bilibili bili_jct'
            and buvid3 != '你的 Bilibili buvid3'):
        credential = Credential(
            sessdata=sessdata, bili_jct=bili_jct, buvid3=buvid3)
    else:
        print_debug('未指定 Bilibili 授权设置！')
        credential = Credential()
    print_debug('完成！')
    return credential


async def fetch_first_page(user: User
                           ) -> tuple[int, list[tuple[str, str, str]]]:
    data = await try_(
        3, lambda: user.get_subscribed_bangumi(1, BangumiType.BANGUMI))
    return (
        ceil(data['total'] / 15),  # 计算并返回总页数
        [(bangumi['media_id'], bangumi['follow_status'], bangumi['progress'])
            for bangumi in data]
    )


async def fetch_page(user: User, page: int) -> list[tuple[str, str, str]]:
    data = await try_(
        3, lambda: user.get_subscribed_bangumi(page, BangumiType.BANGUMI))
    return [(bangumi['media_id'], bangumi['follow_status'],
             bangumi['progress'])
            for bangumi in data]


async def fetch_bangumi_title(credential: Credential, bangumi: int) -> str:
    return (Bangumi(media_id=bangumi, credential=credential)
            .get_meta()["media"]["title"])
