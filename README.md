# Bilibili2Bangumi ![GitHub](https://img.shields.io/github/license/wopub/Bilibili2Bangumi)

将 [Bilibili](https://www.bilibili.com/) 订阅动画迁移至 [Bangumi](https://bgm.tv/)，并保留原追番状态。

欢迎 PR。

## 安装

该程序运行在 [Python](https://www.python.org/) **3.7+** 并要求安装 `pip`。

首先克隆或下载 [Bilibili2Bangumi](https://github.com/wopub/Bilibili2Bangumi) 仓库并切换到程序根目录：

```sh
$ git clone https://github.com/wopub/Bilibili2Bangumi.git
$ cd Bilibili2Bangumi
```

### 依赖安装

#### Pipenv(推荐)

如果没有安装包管理器 [`pipenv`](https://pipenv.pypa.io/en/latest/) ，请安装：

```sh
$ pip install pipenv
```

再安装依赖包：

```sh
$ pipenv install
```

或者使用清华大学开源软件镜像源：

```sh
$ pipenv install --pypi-mirror https://pypi.tuna.tsinghua.edu.cn/simple
```

#### Pip

```sh
$ pip install -r requirements.txt
```

## 使用

先按下述修改完配置文件。

如果使用了 Pipenv 来安装依赖则通过 Pipenv 运行：
   
```sh
$ pipenv run python bili2bgm.py
```   

或者如果使用了 Pip 来安装依赖则直接运行：

```sh
$ python bili2bgm.py
```

程序运行时会显示当前进度和因各种原因而迁移失败的数据。

### 修改配置文件 `config.py`

将仓库根目录下 `config.py.example` 修改为 `config.py`。之后按下述配置参数。

1. bilibili_api 授权设置：
   
   在 `config.py` 中填入需要迁移用户的 `Bilibili UID`。
   
   如果要迁移 **隐私设置未公开** 的 Bilibili 追番数据，则需要获取`身份验证信息`，获取方法[详见此处](https://www.passkou.com/bilibili-api/#/get-credential)。
   
   获取后在 `config.py` 中填入 `SESSDATA`、`BILI_JCT` 和 `BUVID3` 信息。

   **注意，请不要泄露这些信息给他人，否则你的账号将可能遭受被盗的风险！**

2. Bangumi API OAuth2 授权配置:
   
   由于 [Bangumi API](https://github.com/bangumi/api/blob/master/docs-raw/How-to-Auth.md) 只提供 Oauth2 授权码方式，需获取并填入 `App ID` 与 `App Secret`：
   
   1. 在 [Bangumi 开发平台](https://bgm.tv/dev/app) 中创建新应用，如下图
   
      ![image](https://user-images.githubusercontent.com/37031767/116994802-c669cc80-ad0b-11eb-9033-f60de4e2471c.png)
      
      类型选 “应用”，其余随意填写
      
      ![image](https://user-images.githubusercontent.com/37031767/116995199-59a30200-ad0c-11eb-99f7-ef361a26e901.png)
   
   
   2. 获取 `App ID` 与 `App Secret`，并将 **回调地址** 设置为 `http://localhost:3000`
      
      **注意，请不要泄露这些信息给他人，否则你的应用权限将可能遭受被盗用的风险！**
   
      ![image](https://user-images.githubusercontent.com/37031767/116995932-493f5700-ad0d-11eb-8403-680840a04023.png)
    
   3. 将 `App ID` 与 `App Secret` 填入 `config.py` 中。

## 致谢

- [bilibili-api](https://github.com/Passkou/bilibili-api)，GPL-3.0 许可证

- [aiohttp](https://github.com/aio-libs/aiohttp)，Apache-2.0 许可证