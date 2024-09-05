文件说明：
    1. get_window_usb.py 文件
        获取window电脑下符合adb协议的usb端口
    2. parse_tools.py 文件
        解析wireshark抓包获取的usb端口数据、解析adb协议
    3. protocol_port.py 文件
        负责adb协议接口的编写
    4. usb_socket.py
        负责创建socket与设备通信

实现功能：
    1. 通过usb端口像android设备发送指定命令。 目前只实现设备的授权和shell命令的功能


主要安装库：
    pip install pyusb
    pip install rsa
    （暂未指定库版本）

 注意事项：
    1. 电脑如果带有adb， 需使用adb kill-server关闭adb进程。
       （usb端口是唯一的， adb-server启动后会导致usb一直被占用）
    2. 需要使用pyusb库， 这个库在window环境下可能用不了，解决办法：
        a. pip install libusb1, 然后打开venv文件夹， 将usb1下的libusb-1.0.dll的文件copy一份到C:\Windows\System32目录下
        b. 访问这个链接下载：https://libusb.sourceforge.io/api-1.0/libusb_api.html
    3. 代码粗糙，很多东西并没有封装与做异常处理。 仅供学习

参考资料：
     https://android.googlesource.com/platform/system/adb
