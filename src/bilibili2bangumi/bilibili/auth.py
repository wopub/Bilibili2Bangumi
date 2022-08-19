from bilibili_api import Credential

from bilibili2bangumi.utilities import print_debug


def auth_bili(sessdata: str, bili_jct: str, buvid3: str):
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
