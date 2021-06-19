from typing import Callable, Coroutine, Union, Tuple
from traceback import format_exception_only

from httpx import get, RequestError


def print_exception(e: Exception, tried_times: int, times: int) -> bool:
    '''异常被引发时打印异常并判断是否退出（True：继续，False：退出）'''
    print('** 异常被引发！')
    print(format_exception_only(type(e), e)[-1], end='')
    if tried_times == times:
        print(f'** {tried_times} 次尝试均失败，退出！')
        return False
    print(f'** 第 {tried_times} 次尝试失败！')
    tried_times += 1
    print(f'** 进行第 {tried_times} 次尝试...')
    return True


def try_for_times(
    times: int,
    func: Callable,
    exception: Union[Exception, Tuple[Exception]]
):
    '''尝试多次'''
    tried_times = 1
    while True:
        try:
            return func()
        except exception as e:
            if print_exception(e, tried_times, times):
                tried_times += 1
                continue
            else:
                raise


async def try_for_times_async(
    times: int,
    func: Callable[[], Coroutine],
    exception: Union[Exception, Tuple[Exception]]
):
    '''尝试多次（异步）'''
    tried_times = 1
    while True:
        try:
            return await func()
        except exception as e:
            if print_exception(e, tried_times, times):
                tried_times += 1
                continue
            else:
                raise


def get_bili2bgm_map():
    '''构造 Bilibili 编号（media） -> Bangumi 编号映射'''
    BANGUMI_DATA_LINK = \
        'https://cdn.jsdelivr.net/npm/bangumi-data@0.3/dist/data.json'
    print('  请求动画数据...')
    bangumi_data = try_for_times(  # 尝试三次
        3,
        lambda: get(BANGUMI_DATA_LINK).json(),
        RequestError
    )
    print('  构造编号映射...')
    bili2bgm_map = {}
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
