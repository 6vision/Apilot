## 一个基于[ChatGPT-on-Wechat](https://github.com/zhayujie/chatgpt-on-wechat)项目的简单插件，直接调用一些实用的api接口！

### 安装

使用管理员口令在线安装即可，参考这里如何[认证管理员](https://www.wangpc.cc/aigc/chatgpt-on-wechat_plugin/)！

```
#installp https://github.com/6vision/Apilot.git
```

安装成功后，根据提示使用`#scanp`命令来扫描新插件，再使用`#enablep Apilot`开启插件，参考下图

<img width="240" src="https://cdn.jsdelivr.net/gh/6vision/PicBED@latest/images/2023/08/12/539fddb2344205e137fd5933b1f5f20f-image-20230812111523205-02596d.png" />
### 配置
直接安装不配置也可以使用一部分接口，部分接口需要配置alapi的token。
复制插件目录的config.json.template文件并重命名为config.json，在alapi_token字段填入申请的token，token申请点击这里[alapi](https://admin.alapi.cn/account/center)
### 使用

对话框发送“早报”、“摸鱼”、"微博热搜"、”任意星座名称”可以直接返回对应的内容！

<img src="https://cdn.jsdelivr.net/gh/6vision/PicBED@latest/images/2023/08/12/227e04d5f08800ef62ea2eb080dfa751-image-20230812110548378-6198d9.png" alt="image-20230812110548378" style="zoom:50%;" />

<img src="https://cdn.jsdelivr.net/gh/6vision/PicBED@latest/images/2023/08/12/534b9bc440c8ecf66d059dda793d2c72-image-20230812110609065-91a85e.png" alt="image-20230812110609065" style="zoom:50%;" />

快递查询格式：快递+快递编号。如：快递YT2505082504474，如下图!
<img src="https://cdn.jsdelivr.net/gh/6vision/PicBED@latest/images/2023/08/25/f8e7c4af26945c41b2e90e14aa2928f6-image-20230825210757913-7673a1.png" alt="image-20230825210757913" style="zoom:50%;" />


