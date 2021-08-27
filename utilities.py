from typing import Any, Callable, Coroutine, Union, Tuple, Type
from traceback import format_exception_only
from json.decoder import JSONDecodeError
from inspect import stack
from asyncio import get_event_loop
from time import sleep

from aiohttp import (
    ClientError, ClientSession, ClientResponseError, ContentTypeError,
    TCPConnector
)

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
    '''打印状态并用空格填充'''
    print('%-80s' % status, **kw)


def print_debug(status: str = '', depth: int = 0, **kw):
    '''打印调试状态（包括当前函数名和行号）并用空格填充'''
    if PRINT_DEBUG_INFORMATION:
        frame = stack()[depth + 1]
        print('%-80s' % (
            '[%s:%d] %s' % (frame.function, frame.lineno, status)
        ), **kw)


def print_exception(
    e: Exception, tried_times: int, times: int
) -> bool:
    '''异常被引发时打印异常'''
    print_status('** 异常：%s' % format_exception_only(type(e), e)[-1], end='')


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
            print_exception(e, tried_times, times)
            if tried_times < times:
                tried_times += 1
                continue
            else:
                raise
        else:
            return result


async def try_get_json(times: int, client: ClientSession, url: str, **kw):
    '''尝试 GET 多次并转换成 JSON'''
    tried_times = 1
    while True:
        try:
            r = await client.get(url, **kw)
            r.raise_for_status()
            return await r.json()
        except ContentTypeError as e:
            print_exception(e, tried_times, times)
            print_debug(f'GET {url}')
            print_debug(kw)
            try:
                print_debug(await r.text())
            except ClientError:
                pass
            if tried_times < times:
                tried_times += 1
                continue
            else:
                raise
        except ClientResponseError as e:
            if e.status == 503:
                print_status('** HTTP 状态 503，别慌，稍等片刻即可')
                sleep(0.5)  # 强行阻塞事件循环
            else:
                print_status(f'** HTTP 状态 {e.status}')
            if tried_times < times:
                tried_times += 1
                continue
            else:
                raise
        except (JSONDecodeError, ClientError) as e:
            print_exception(e, tried_times, times)
            print_debug(f'GET {url}')
            print_debug(kw)
            try:
                print_debug(await r.text())
            except ClientError:
                pass
            if tried_times < times:
                tried_times += 1
                continue
            else:
                raise


async def try_post_json(
    times: int, client: ClientSession, url: str, *, data, **kw
):
    '''尝试 POST 多次并转换成 JSON'''
    tried_times = 1
    while True:
        try:
            r = await client.post(url, data=data, **kw)
            r.raise_for_status()
            return await r.json()
        except ContentTypeError as e:
            print_exception(e, tried_times, times)
            print_debug(f'POST {url}')
            print_debug(data)
            print_debug(kw)
            try:
                print_debug(await r.text())
            except ClientError:
                pass
            if tried_times < times:
                tried_times += 1
                continue
            else:
                raise
        except ClientResponseError as e:
            if e.status == 503:
                print_status('** HTTP 状态 503，别慌，稍等片刻即可')
                sleep(0.5)  # 强行阻塞事件循环
            else:
                print_status(f'** HTTP 状态 {e.status}')
            if tried_times < times:
                tried_times += 1
                continue
            else:
                raise
        except (JSONDecodeError, ClientError) as e:
            print_exception(e, tried_times, times)
            print_debug(f'POST {url}')
            print_debug(data)
            print_debug(kw)
            try:
                print_debug(await r.text())
            except ClientError:
                pass
            if tried_times < times:
                tried_times += 1
                continue
            else:
                raise


async def get_bili2bgm_map():
    '''构造 Bilibili 编号（media） -> (Bangumi 编号, 标题) 映射'''
    BANGUMI_DATA_LINK = \
        'https://cdn.jsdelivr.net/npm/bangumi-data@0.3/dist/data.json'
    print_debug('请求动画数据...')
    bangumi_data = await try_get_json(  # 尝试三次
        3, client, BANGUMI_DATA_LINK
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
