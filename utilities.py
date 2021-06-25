from typing import Callable, Coroutine, Union, Tuple
from traceback import format_exception_only
from json.decoder import JSONDecodeError
from inspect import stack

from aiohttp import ClientError, ClientSession, TCPConnector

from config import CONNECTION_LIMIT_PER_HOST, PRINT_DEBUG_INFORMATION

client = ClientSession(
    connector=TCPConnector(limit_per_host=CONNECTION_LIMIT_PER_HOST),
    headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0)'
        ' Gecko/20100101 Firefox/89.0'
    }
)


def print_status(status, depth=0, **kw):
    '''打印状态（包括当前函数名）并用空格填充'''
    print('%-80s' % ('[%s] %s' % (stack()[depth + 1].function, status)), **kw)

def print_debug(status, depth=0, **kw):
    '''打印调试状态（包括当前函数名）并用空格填充'''
    if PRINT_DEBUG_INFORMATION:
        print_status('[debug] ' + status, depth + 1, **kw)


def print_exception(e: Exception, tried_times: int, times: int) -> bool:
    '''异常被引发时打印异常并判断是否退出（True：继续，False：退出）'''
    print_status('** 异常被引发！', 2)
    print_status('** %s' % format_exception_only(type(e), e)[-1], 2, end='')
    if tried_times == times:
        print_status(f'** {tried_times} 次尝试均失败，退出！', 2)
        return False
    print_status(f'** 第 {tried_times} 次尝试失败！', 2)
    tried_times += 1
    print_status(f'** 进行第 {tried_times} 次尝试...', 2)
    return True


async def try_for_times_async_chain(
    times: int,
    func: Callable[[], Coroutine],
    *func_chain: Callable[[], Coroutine],
    exception: Union[Exception, Tuple[Exception]] = ClientError
):
    '''尝试多次'''
    tried_times = 1
    while True:
        try:
            result = await func()
            for f in func_chain:
                result = await f(result)
        except exception as e:
            if print_exception(e, tried_times, times):
                tried_times += 1
                continue
            else:
                raise
        else:
            return result


async def try_for_times_async_json(
    times: int,
    func: Callable[[], Coroutine],
    exception: Union[Exception, Tuple[Exception]] = (
        ClientError, JSONDecodeError
    )
):
    '''尝试多次并转换成 JSON'''
    return await try_for_times_async_chain(
        times,
        func,
        lambda r: r.json(),
        exception=exception
    )


async def get_bili2bgm_map():
    '''构造 Bilibili 编号（media） -> (Bangumi 编号, 标题) 映射'''
    BANGUMI_DATA_LINK = \
        'https://cdn.jsdelivr.net/npm/bangumi-data@0.3/dist/data.json'
    print_status('请求动画数据...')
    bangumi_data = await try_for_times_async_json(  # 尝试三次
        3,
        lambda: client.get(BANGUMI_DATA_LINK)
    )
    print_status('构造映射...')
    bili2bgm_map = {}
    for bangumi in bangumi_data['items']:
        bili_id = bgm_id = None
        if 'zh-Hans' in bangumi['titleTranslate']:
            title = bangumi['titleTranslate']['zh-Hans'][0]
        else:
            title = bangumi['title']
        for site in bangumi['sites']:
            name = site['site']
            if name == 'bilibili':
                bili_id = int(site['id'])
            elif name == 'bangumi':
                bgm_id = site['id']
            else:
                continue
            if bili_id is not None and bgm_id is not None:
                break
        if bili_id is not None:
            bili2bgm_map[bili_id] = (bgm_id, title)
    print_status('完成！')
    return bili2bgm_map
