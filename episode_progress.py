from re import match
from typing import Optional


def parse_episode_progress(progress: str) -> Optional[int]:
    if progress == '':
        return None
    elif progress.startswith('看到'):
        m = match(r'看到第(\d+)话.*', progress)
        if m is not None:
            ep = int(m.group(1))
            if ep == 1:
                return None
            else:
                return ep - 1
        return None
    elif progress.startswith('已看完'):
        if progress == '已看完全片':
            return 1
        m = match(r'已看完第(\d+)话.*', progress)
        if m is not None:
            return int(m.group(1))
        return None
    return None


def test_parse_episode_progress():
    assert parse_episode_progress('') is None
    assert parse_episode_progress('看到第3话') == 2
    assert parse_episode_progress('看到全片') is None
    assert parse_episode_progress('看到第12话 23:26') == 11
    assert parse_episode_progress('看到小剧场13 0:42') is None
    assert parse_episode_progress('看到总集篇 0:27') is None
    assert parse_episode_progress('看到正式PV 1:58') is None
    assert parse_episode_progress('看到全片 1:54') is None
    assert parse_episode_progress('看到第1话 2:42:51') is None
    assert parse_episode_progress('看到第2话 2:42:51') == 1
    assert parse_episode_progress('看到') is None
    assert parse_episode_progress('已看完第40话') == 40
    assert parse_episode_progress('已看完全片') == 1
    assert parse_episode_progress('已看完13(OVA)') is None
    assert parse_episode_progress('已看完') is None
