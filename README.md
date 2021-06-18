# 说明

之前为了将 B 站看过的动画迁移到 bangumi 写的, 本来只是自己用, 但公开可能对其他人会有帮助。

仓库最近无法维护, 程序有很多缺点, 欢迎 PR 和 Contributors。

## 使用说明

1. Python 版本要求：

   `Python 3.7+` 并安装了 `pip`

   如果没有安装包管理器 `pipenv` 就先安装它：

   ```sh
   $ pip install pipenv
   ```

2. 安装依赖包：

   ```sh
   $ pipenv install
   ```

   或者使用清华大学开源软件镜像源：

   ```sh
   $ pipenv install --pypi-mirror https://pypi.tuna.tsinghua.edu.cn/simple
   ```

3. 配置 Bilibili UID： 
  
   在 `bili2bgm.py` 18 行中填入 `Bilibili UID`
   
   ```python
   # 基础设置，必填
   BILI_UID = "你的 Bilibili UID"
   ```

4. 配置 bilibili_api：
   
   如果 Bilibili 个人隐私设置为 **不公开** 番剧观看信息，则需要获取 Credential 类所需信息，获取方法参见 [bilibili_api 文档](https://www.passkou.com/bilibili-api/#/get-credential)

   **注意，请不要泄露这些信息给他人，否则你的账号将可能遭受被盗的风险！**
   
   获取后在 `bili2bgm.py` 21-23 行中填入 `SESSDATA`、`bili_jct` 与 `buvid3`
   
   ```python
   # bilibili_api 授权设置，选填（开启隐私设置则必填）
   SESSDATA = "你的 SESSDATA"
   BILI_JCT = "你的 bili_jct"
   BUVID3 = "你的 buvid3"
   ```

5. Bangumi API OAuth2 授权配置:
   
   需获取并填入 `App ID` 与 `App Secret`
   
   下面是获取方法:
   
   1. 在 [Bangumi 开发平台](https://bgm.tv/dev/app) 中创建新应用，如下图
   
      ![image](https://user-images.githubusercontent.com/37031767/116994802-c669cc80-ad0b-11eb-9033-f60de4e2471c.png)
      
      类型选 “应用”，其余随意填写
      
      ![image](https://user-images.githubusercontent.com/37031767/116995199-59a30200-ad0c-11eb-99f7-ef361a26e901.png)
   
   
   2. 获取 `App ID` 与 `App Secret`，并将 **回调地址** 设置为 `http://localhost:3000`
      
      **注意，请不要泄露这些信息给他人，否则你的应用权限将可能遭受被盗用的风险！**
   
      ![image](https://user-images.githubusercontent.com/37031767/116995932-493f5700-ad0d-11eb-8403-680840a04023.png)
    
   3. 将 `App ID` 与 `App Secret` 填入 `bili2bgm.py` 26-27 行中：

      ```python
      # Bangumi OAuth2 授权设置，必填
      APP_ID = '你的 App ID'
      APP_SECRET = '你的 App Secret'
      ```

6. 在完成上述步骤后，运行程序：
   
   ```sh
   $ python bili2bgm.py
   ```
