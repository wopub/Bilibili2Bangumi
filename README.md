# Bilibili2Bangumi ![GitHub](https://img.shields.io/github/license/wopub/Bilibili2Bangumi)

将 [Bilibili](https://www.bilibili.com/) 订阅动画迁移至 [Bangumi](https://bgm.tv/)，保留原追番状态并自动点格子。

欢迎 PR。

## 安装

该程序运行在 [Python](https://www.python.org/) **3.7+** 并要求安装 `pip`。

首先克隆或下载 [Bilibili2Bangumi](https://github.com/wopub/Bilibili2Bangumi) 仓库并切换到程序根目录：

```sh
$ git clone https://github.com/wopub/Bilibili2Bangumi.git
$ cd Bilibili2Bangumi
```

bilibili2bangumi 使用 Poetry 来管理依赖，请先[安装 Poetry](https://python-poetry.org/docs/#installation)，然后执行以下命令：

```sh
$ poetry install
```

## 使用

先按下述修改完配置文件，然后执行以下命令：
   
```sh
$ poetry run main
```

程序运行时会显示当前进度和因各种原因而迁移失败的数据。

### 修改配置文件 `config.py`

将仓库根目录下 `config.py.example` 修改为 `config.py`。之后按下述配置参数。

1. bilibili_api 授权设置：
   
   在 `config.py` 中填入需要迁移用户的 `Bilibili UID`。
   
   获取身份验证信息，获取方法[详见此处](https://www.passkou.com/bilibili-api/#/get-credential)。获取后在 `config.py` 中填入 `SESSDATA`、`BILI_JCT` 和 `BUVID3` 信息。

   **注意，请不要泄露这些信息给他人，否则你的账号将可能遭受被盗的风险！**

2. 其他设置：
   
   `bool` 类型的设置请填入 `True`（启用）或 `False`（禁用），`int` 类型的设置请填入整数。

   | 名称                          | 说明                                                                           | 类型   | 默认值  |
   | ----------------------------- | ------------------------------------------------------------------------------ | ------ | ------- |
   | PARSE_EPISODE_PROGRESS        | 自动点在看动画的格子（无论隐私设置如何都必须填写 bilibili_api 授权设置才有效） | `bool` | `True`  |
   | SKIP_COLLECTED                | 跳过更新已更新动画的收藏状态                                                   | `bool` | `True`  |
   | OPEN_FAILED_BANGUMI_BILI_PAGE | 自动打开更新失败的动画的页面（可能会一次性弹出非常多页面）                     | `bool` | `False` |
   | CONNECTION_LIMIT_PER_HOST     | 每站点最大并发连接数（越多越快，但太多可能会导致服务器不可用）                 | `int`  | `15`    |
   | PRINT_DEBUG_INFORMATION       | 打印调试信息，***调试用***                                                       | `bool` | `False` |
   | DRY_RUN                     | 只打印信息而不实际进行更新操作，***调试用***                                     | `bool` | `False` |

## 致谢

- [Bilibili](https://www.bilibili.com/) & [Bangumi](https://bgm.tv/)

- [Bangumi-data](https://github.com/bangumi-data/bangumi-data)，CC-BY-4.0 许可证

- [bilibili-api](https://github.com/Passkou/bilibili-api)，GPL-3.0 许可证

- [aiohttp](https://github.com/aio-libs/aiohttp)，Apache-2.0 许可证