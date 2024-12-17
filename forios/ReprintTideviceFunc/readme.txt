2024/09/11
文件说明：
    1. get_device_applist.py 文件
       实现模拟tidevice applist命令底层原理
    2. get_ios_infomation.py 文件
       实现模拟tidevice list命令底层实现原理
    3. get_ios_launch.py 文件
       实现模拟tidevice launch命令底层原理
    4. ios17_get_address.py 文件
       实现模拟获取ios17系统需要的指定通信地址底层原理

实现功能：
    1. 模拟与ios设备通信交互原理


主要安装库：
    python 3.9.11
    pip install tidevice（寄人篱下，调用了tidevice的dtx协议的定义）

注意事项：
*** 必须安装itunes哈，或者爱思，不然有报错
    1. 基本使用python原装库就可以运行， 调用拉起app操作的时候，偷懒使用了tidevice封装的dtx协议规范
    2. ios17需要先向设备交互获取一个通信地址， 并且要给他创建一个“网络适配器”， 这里只是简单演示如何请求获取指定的通信地址

*** 说白了我是copy tidevice，pymobiledevice3源码的一些方法，只是把实现思路拆分出来了，可以进一步了解与ios设备通信的原理


参考资料：
     https://github.com/doronz88/pymobiledevice3
     https://github.com/alibaba/tidevice
