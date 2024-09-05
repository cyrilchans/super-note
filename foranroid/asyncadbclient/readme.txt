2024/09/06
文件说明：
    1.  adb_core.py
        实现adb-client与adb-server交互的命令封装
    2.  adb_manager.py
        对adb命令的一些封装。
    3.  mixed_filed.py
        一些关键协议头以及一些无关重要

实现功能：
    1.  使用异步模拟实现adb-client端像adb-server发送命令的过程
    2.  实现命令：
        adb start-server
        adb devices
        adb push
        adb pull
        adb start_app
        adb stop_app
        adb clear_app
        adb shell
        adb install
        adb uninstall


主要安装库：
    python 3.9.11

注意事项：
    1. 细节未处理， 主要演示adb-client如果实现与adb-server通信
    2. 其实完全没必要异步， 设备多了异步有坑
参考资料：
    https://github.com/openatx/adbutils
