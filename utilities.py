from re import L
from typing import Any, Callable, Coroutine, Union, Tuple, Type
from traceback import format_exception_only
from json.decoder import JSONDecodeError
from inspect import stack
from asyncio import get_event_loop

from aiohttp import ClientError, ClientSession, TCPConnector

from config import CONNECTION_LIMIT_PER_HOST, PRINT_DEBUG_INFORMATION

loop = get_event_loop()

client = ClientSession(
    connector=TCPConnector(
        limit_per_host=CONNECTION_LIMIT_PER_HOST,
        loop=loop
    ),
    headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0)'
        ' Gecko/20100101 Firefox/89.0'
    }
)


def print_status(status: str, **kw):
    '''打印状态（包括当前函数名）并用空格填充'''
    print('%-80s' % status, **kw)


def print_debug(status: str = '', depth: int = 0, **kw):
    '''打印调试状态（包括当前函数名和行号）并用空格填充'''
    if PRINT_DEBUG_INFORMATION:
        frame = stack()[depth + 1]
        print('%-80s' % (
            '[%s:%d] %s' % (frame.function, frame.lineno, status)
        ), **kw)


def print_exception(
    e: Exception, tried_times: int, times: int, depth: int = 0
) -> bool:
    '''异常被引发时打印异常并判断是否退出（True：继续，False：退出）'''
    if tried_times == times:
        print_status('** 异常被引发！')
        print_status('** %s' % format_exception_only(type(e), e)[-1], end='')
        print_status(f'** {tried_times} 次尝试均失败，退出！')
        return False
    else:
        print_debug('** 异常被引发！', depth + 1)
        print_debug(
            '** %s' % format_exception_only(type(e), e)[-1],
            depth + 1, end=''
        )
        print_debug(f'** 第 {tried_times} 次尝试失败！', depth + 1)
        tried_times += 1
        print_debug(f'** 进行第 {tried_times} 次尝试...', depth + 1)
        return True


async def try_for_times_async_chain(
    times: int,
    func: Callable[[], Coroutine],
    *func_chain: Callable[[Any], Coroutine],
    exception: Union[
        Type[Exception], Tuple[Type[Exception], ...]
    ] = ClientError,
    depth: int = 0
):
    '''尝试多次'''
    tried_times = 1
    while True:
        try:
            result = await func()
            for f in func_chain:
                result = await f(result)
        except exception as e:
            if print_exception(e, tried_times, times, depth + 1):
                tried_times += 1
                continue
            else:
                raise
        else:
            return result


async def try_for_times_async_json(
    times: int,
    func: Callable[[], Coroutine],
    exception: Union[Type[Exception], Tuple[Type[Exception], ...]] = (
        ClientError, JSONDecodeError
    ),
    depth: int = 0
):
    '''尝试多次并转换成 JSON'''
    return await try_for_times_async_chain(
        times,
        func,
        lambda r: r.json(),
        exception=exception,
        depth=depth+1
    )


async def get_bili2bgm_map():
    '''构造 Bilibili 编号（media） -> (Bangumi 编号, 标题) 映射'''
    BANGUMI_DATA_LINK = \
        'https://cdn.jsdelivr.net/npm/bangumi-data@0.3/dist/data.json'
    print_debug('请求动画数据...')
    bangumi_data = await try_for_times_async_json(  # 尝试三次
        3,
        lambda: client.get(BANGUMI_DATA_LINK)
    )
    print_debug('构造映射...')
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
    print_debug('完成！')
    return bili2bgm_map
