# Bilibili2Bangumi ![GitHub](https://img.shields.io/github/license/wopub/Bilibili2Bangumi)

将 [Bilibili](https://www.bilibili.com/) 已看过的动画迁移至 [Bangumi](https://bgm.tv/)。

欢迎 PR。

## 安装

该程序运行在 [Python](https://www.python.org/) **3.7+** 并要求安装 `pip`。

首先克隆或下载 [Bilibili2Bangumi](https://github.com/wopub/Bilibili2Bangumi) 仓库并切换到程序根目录：

```sh
$ git clone https://github.com/wopub/Bilibili2Bangumi.git
$ cd Bilibili2Bangumi
```

如果没有安装包管理器 `pipenv` 就安装它：

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

## 使用

按下述修改完配置文件后，运行程序：
   
```sh
$ pipenv run python bili2bgm.py
```

程序运行时会显示当前进度和因各种原因而迁移失败的数据。

### 修改配置文件 `config.py`

1. bilibili_api 授权设置：
   
   在 `config.py` 中填入需要迁移用户的 `Bilibili UID`。
   
   如果 Bilibili 个人隐私设置为 **不公开** 番剧观看信息，则需要获取`身份验证信息`，获取方法[详见此处](https://www.passkou.com/bilibili-api/#/get-credential)。
   
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
