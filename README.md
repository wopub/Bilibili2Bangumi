# 说明

之前为了将B站看过的动画迁移到bangumi写的, 本来只是自己用, 但公开可能对其他人会有帮助.

仓库最近无法维护, 程序有很多缺点, 欢迎 PR 和 Contributors

## 使用说明

1. Python版本要求：`Python 3.8+`

2. 使用前安装依赖包：

    ```
    pip install -r requirements.txt
    ```

3. 配置 Bilibili-API ：
   
   如果 Bilibili 个人隐私设置 **不公开** 番剧观看信息，则需要获取`身份验证信息`，获取方法[详见此处](https://github.com/Passkou/bilibili-api/blob/main/README.md#%E8%8E%B7%E5%8F%96-sessdata-%E5%92%8C-csrf)
   
   获取后在 `bili2bangumi.py` 中填入 `sessdata` 、`csrf` 信息
   
   ```
    # bili2bangumi.py 第 22 行：

      uid = 12345                    # Bilibili 用户 ID，必填
      sessdata = "此处填入 sessdata"  # 填入 sessdata，选填
      csrf = "此处填入 csrf"          # 填入 csrf ，选填
   ```


4. Bangumi API OAuth2 授权配置:
   
   需获取并填入 `client_id` 与 `client_secret`
   
   下面是获取方法:
   
    1. 在 [Bangumi 开发平台](https://bgm.tv/dev/app) 中创建新应用，如下图
   
   > ![image](https://user-images.githubusercontent.com/37031767/116994802-c669cc80-ad0b-11eb-9033-f60de4e2471c.png)
   >
   >  - 类型选 “应用”，其余随意填写
   >
   > ![image](https://user-images.githubusercontent.com/37031767/116995199-59a30200-ad0c-11eb-99f7-ef361a26e901.png)
   
   
    2. 获取 `App ID` 与 `App Secret` ，
       
       并将 **回调地址** 设置为 `http://localhost:3000`
   
   > ![image](https://user-images.githubusercontent.com/37031767/116995932-493f5700-ad0d-11eb-8403-680840a04023.png)
    
    3. 将 `App ID` 与 `App Secret` 填入 `bili2bangumi.py` 中：

      ```
        # bili2bangumi.py 第 28 行

         client_id = '此处填入 App ID'          # 必填，填入 App ID
         client_secret = '此处填入 App Secret'  # 必填，填入 App Secret
      ```

5. 在完成上述步骤后，运行程序：
   
   ```
      python bili2bangumi.py
   ```