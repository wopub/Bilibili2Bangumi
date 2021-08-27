from utilities import loop, client, print_debug, print_status, get_bili2bgm_map
from auth import auth_bili, auth_bgm
from update import get_and_update
from config import BILI_UID, SESSDATA, BILI_JCT, BUVID3, APP_ID, APP_SECRET


async def main():
    if BILI_UID == '你的 Bilibili UID':
        print_status('** 未指定 Bilibili UID！')
        exit(1)
    if (
        APP_ID == '你的 Bangumi App ID'
        and APP_SECRET == '你的 Bangumi App Secret'
    ):
        print_status('** 未指定 Bangumi 授权设置！')
        exit(1)

    print_debug('创建构造编号映射任务 -> [get_bili2bgm_map]')
    get_bili2bgm_map_task = loop.create_task(get_bili2bgm_map())

    print_debug('创建取得 Bilibili 授权任务 -> [auth_bili]')
    auth_bili_task = loop.create_task(auth_bili(SESSDATA, BILI_JCT, BUVID3))

    print_debug('创建取得 Bangumi 授权任务 -> [auth_bgm]')
    auth_bgm_task = loop.create_task(auth_bgm(APP_ID, APP_SECRET))

    print_debug('等待任务...')
    bili2bgm_map = await get_bili2bgm_map_task
    bili_auth_data = await auth_bili_task
    bgm_auth_data, bgm_user_id = await auth_bgm_task

    print_status('正在迁移...')
    print_debug('等待更新数据任务 -> [get_and_update]')
    await get_and_update(
        bili2bgm_map, bili_auth_data, BILI_UID, bgm_auth_data, bgm_user_id
    )


if __name__ == '__main__':
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print('\n已取消！')
    except SystemExit:
        print('\n失败！')
        raise
    else:
        print('\n完成！')
    finally:
        loop.run_until_complete(client.close())
