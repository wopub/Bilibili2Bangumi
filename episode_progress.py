from re import match
from typing import Optional


def parse_episode_progress(progress: str) -> Optional[int]:
    if progress == '':
        return None
    elif progress.startswith('看到'):
        m = match('看到第(\d+)话.*', progress)
        if m is not None:
            ep = int(m.group(0))
            if ep == 1:
                return None
            else:
                return ep - 1
        return None
    elif progress.startswith('已看完'):
        if progress == '已看完全片':
            return 1
        else:
            m = match('已看完第(\d+)话.*', progress)
            if m is not None:
                return int(m.group(0))
            return None
