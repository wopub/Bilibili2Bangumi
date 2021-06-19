from asyncio import get_event_loop

from utilities import get_bili2bgm_map
from auth import auth_bili, auth_bgm
from update import get_and_update
from settings import BILI_UID, SESSDATA, BILI_JCT, BUVID3, APP_ID, APP_SECRET


def main():
    print('构造 Bilibili 编号 -> Bangumi 编号映射...')
    bili2bgm_map = get_bili2bgm_map()
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
        print('\n已取消！')
    else:
        print('完成！')
