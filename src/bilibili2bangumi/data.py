from collections import deque


class Bili2BgmData:
    '''存放所有中间数据的类'''

    bili2bgm_map = None
    '''Bilibili 至 Bangumi 编号映射'''

    user = None
    '''Bilibili 用户'''

    bili_auth_data = None
    '''Bilibili 验证信息'''

    bgm_auth_data = None
    '''Bangumi 验证信息'''

    bgm_user_id = None
    '''Bangumi 用户名'''

    bili_processed_count: int = 0
    '''Bilibili 已处理条目数'''

    bili_total_count = None
    '''Bilibili 总共条目数'''

    bangumi_total: int = 0
    '''Bangumi 总共条目数'''

    bangumi_remaining = deque()
    '''Bangumi 待处理条目 [(bili media id, 1: 想看 | 2: 在看 | 3: 看过), ...]'''

    bangumi_processed_count: int = 0
    '''Bangumi 已处理条目数'''

    bangumi_failed = deque()
    '''Bangumi 失败条目'''

    bangumi_failed_count = 0
    '''Bangumi 失败条目数'''

    animation_points = 1
    '''进度条动画中的点的数量'''

    get_bili_data_task = None
    '''Bilibili 获取任务'''

    update_bgm_data_task = None
    '''Bangumi 更新异步任务'''

    update_one_bgm_data_tasks = deque()
    '''Bangumi 单个更新异步任务'''

    print_unknown_tasks = deque()
    '''进度条动画点数'''
