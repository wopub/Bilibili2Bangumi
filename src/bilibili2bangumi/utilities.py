from typing import Any, Callable, Coroutine, Optional, Union, Tuple, Type
from traceback import format_exception_only
from json.decoder import JSONDecodeError
import inspect
import asyncio
import time

import aiohttp
from aiohttp import (
    ClientError, ClientSession, ClientResponseError, ContentTypeError,
    TCPConnector, __version__ as aiohttp_version
)

from bilibili2bangumi import __version__ as bilibili2bangumi_version
from bilibili2bangumi.config import CONNECTION_LIMIT_PER_HOST, PRINT_DEBUG_INFORMATION

LOOP = asyncio.get_event_loop()

CLIENT = ClientSession(
    connector=TCPConnector(
        limit_per_host=CONNECTION_LIMIT_PER_HOST,
        loop=LOOP
    ),
    headers={
        'User-Agent': f'Bilibili2Bangumi/{bilibili2bangumi_version}'
        f' (https://github.com/wopub/Bilibili2Bangumi)'
        f' aiohttp/{aiohttp_version}'
    }
)


def print_status(status: str, **kw):
    '''打印状态并用空格填充'''
    print(f'{status:-80s}', **kw)


def print_debug(status: str = '', depth: int = 0, **kw):
    '''打印调试状态（包括当前函数名和行号）并用空格填充'''
    if PRINT_DEBUG_INFORMATION:
        frame = inspect.stack()[depth + 1]
        print_status(f'[{frame.function}:{frame.lineno}] {status}', **kw)


def print_exception(e: Exception):
    '''异常被引发时打印异常'''
    print_status('** 异常：%s' % format_exception_only(type(e), e)[-1], end='')


async def try_(
    times: int,
    function: Callable[[], Coroutine],
    *functions: Callable[[Any], Coroutine],
    excepted: Union[
        Type[Exception], Tuple[Type[Exception], ...]
    ] = ClientError
) -> Any:
    '''尝试 await 指定的次数'''
    tried_times = 1
    while True:
        try:
            result = await function()
            for f in functions:
                result = await f(result)
        except excepted as exc:
            print_exception(exc)
            if tried_times < times:
                tried_times += 1
                continue
            else:
                raise
        else:
            return result


async def handle_exception(r: aiohttp.ClientResponse, exc: Exception,
                           **kw: Any) -> bool:
    if (isinstance(exc, ClientResponseError)
            and not isinstance(exc, ContentTypeError)):
        if exc.status == 503:
            print_status('** HTTP 状态 503，别慌，稍等片刻')
            time.sleep(0.5)  # 强行阻塞事件循环
        else:
            print_status(f'** HTTP 状态 {exc.status}')
    elif isinstance(exc, (ContentTypeError, JSONDecodeError, ClientError)):
        print_exception(exc)
        if isinstance(exc, ContentTypeError):
            print_debug(
                f'{exc.request_info.method} {exc.request_info.real_url}')
            print_debug(f'headers = {exc.request_info.headers}')
            print_debug(f'kw = {kw}')
        try:
            print_debug(await r.text())
        except ClientError:
            pass
    else:
        return False
    return True


async def try_get_json(times: int, client: ClientSession, url: str, **kw):
    '''尝试 GET 多次并转换成 JSON'''
    tried_times = 1
    while True:
        try:
            r = await client.get(url, **kw)
            r.raise_for_status()
            return await r.json()
        except (JSONDecodeError, ClientError) as exc:
            await handle_exception(r, exc, **kw)
            if tried_times < times:
                tried_times += 1
                continue
            else:
                raise


async def try_post_json(times: int, client: ClientSession, url: str, *,
                        data: Any = None, **kw: Any):
    '''尝试 POST 多次并转换成 JSON'''
    tried_times = 1
    while True:
        try:
            r = await client.post(url, data=data, **kw)
            r.raise_for_status()
            return await r.json()
        except (JSONDecodeError, ClientError) as exc:
            await handle_exception(r, exc, **kw)
            if tried_times < times:
                tried_times += 1
                continue
            else:
                raise


async def get_bili2bgm_map() -> dict[int, tuple[Optional[str], str]]:
    '''构造 Bilibili 编号（media） -> (Bangumi 编号, 标题) 映射'''
    BANGUMI_DATA_LINK = \
        'https://cdn.jsdelivr.net/npm/bangumi-data@0.3/dist/data.json'
    print_debug('请求动画数据...')
    bangumi_data = await try_get_json(3, CLIENT, BANGUMI_DATA_LINK)
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
