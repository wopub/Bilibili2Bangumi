# 说明

之前为了将B站看过的动画迁移到bangumi写的, 本来只是自己用, 但公开可能对其他人会有帮助.

仓库最近无法维护, 程序有很多缺点, 欢迎 PR 和 Contributors

## 使用说明

python 3.8+
1. 安装依赖

    ```
    pip install -r requirements.txt
    ```

2. 配置bilibili-api `sessdata` `csrf` 
   ```
    uid = 12882825  # bangumi 用户id(整型), 必填
    sessdata = ""  # verify 字段
    csrf = ""  # verify 字段
   ```
   如果未公开观看信息，则需要获得登录字段，[详见此处](https://github.com/Passkou/bilibili-api/blob/main/README.md#%E8%8E%B7%E5%8F%96-sessdata-%E5%92%8C-csrf)
3. bangumi api oauth2授权 `oauth2` `client_id` `client_secret`
   1. 在[bangmu开发平台](https://bgm.tv/dev/app)创建应用
   ![image](https://user-images.githubusercontent.com/47666274/116972266-5ba99880-aced-11eb-8553-bcf540f5641f.png)
   2. 获取 `App ID` 与 `App Secret` 分别填入 `client_id` `client_secret`
4. 运行程序
