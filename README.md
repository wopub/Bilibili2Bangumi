# 说明

之前为了将B站看过的动画迁移到bangumi写的, 本来只是自己用, 但公开可能对其他人会有帮助.

仓库最近无法维护, 程序有很多缺点, 欢迎 PR 和 Contributors

## 使用说明

python 3.8+

1. 获取B站登录信息, [详见此处](https://github.com/Passkou/bilibili-api/blob/main/README.md#%E8%8E%B7%E5%8F%96-sessdata-%E5%92%8C-csrf) `sessdata` `csrf` 
2. bangumi api oauth2授权(待补充) `oauth2` `client_id` `client_secret`
3. 运行程序(需要两次, 第一次获取授权, 第二次正式运行) `uid`