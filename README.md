# Bilibili2Bangumi

将 [Bilibili](https://www.bilibili.com/) 已看过的动画迁移至 [Bangumi](https://bgm.tv/)。

仓库最近无法维护, 程序有很多缺点, 欢迎 PR 和 Contributors

## 安装

首先克隆或下载 [Bilibili2Bangumi](https://github.com/wopub/Bilibili2Bangumi) 仓库：

```
git clone https://github.com/wopub/Bilibili2Bangumi.git
```

切换到程序根目录并开始安装依赖文件：

```
pip install -r requirements.txt
```

该程序运行在 [Python](https://www.python.org/) **3.x**。

## 使用

按下述修改完配置文件后，运行程序：
   
```
python b2b.py
```

### 修改配置文件 `config.py`

1. 配置 Bilibili-API ：
   
   设置需要迁移用户的 Bilibili `UID`。
   
   如果 Bilibili 个人隐私设置为 **不公开** 番剧观看信息，则需要获取`身份验证信息`，获取方法[详见此处](https://github.com/Passkou/bilibili-api/blob/main/README.md#%E8%8E%B7%E5%8F%96-sessdata-%E5%92%8C-csrf)。
   
   获取后在 `config.py` 中填入 `SESSDATA` 、`CSRF` 信息。

2. Bangumi API OAuth2 授权配置:
   
   由于 [bangumi-api](https://github.com/bangumi/api/blob/master/docs-raw/How-to-Auth.md) 只提供 Oauth2 授权码方式，需获取并填入 `CLIENT_ID` 与 `CLIENT_SECRET`。
   
   下面是获取方法:
   
   1. 在 [Bangumi 开发平台](https://bgm.tv/dev/app) 中创建新应用，如下图
   
      ![image](https://user-images.githubusercontent.com/37031767/116994802-c669cc80-ad0b-11eb-9033-f60de4e2471c.png)
      
      类型选 “应用”，其余随意填写
      
      ![image](https://user-images.githubusercontent.com/37031767/116995199-59a30200-ad0c-11eb-99f7-ef361a26e901.png)
   
   
   2. 获取 `App ID` 与 `App Secret` ，
       
      并将 **回调地址** 设置为 `http://localhost:3000`
   
      ![image](https://user-images.githubusercontent.com/37031767/116995932-493f5700-ad0d-11eb-8403-680840a04023.png)
    
   3. 将 `App ID` 与 `App Secret` 填入 `config.py` 中：

      ```
      # bangumi oauth2 config
      CLIENT_ID: str = '此处填入 App ID'          # 必填，填入 App ID
      CLIENT_SECRET: str = '此处填入 App Secret'  # 必填，填入 App Secret
      ```
