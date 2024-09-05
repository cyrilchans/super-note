from foranroid.asyncadbclient.adb_manager import AdbDevice

if __name__ == '__main__':
    adb = AdbDevice("127.0.0.1", 5037)  # Connect to tcp:localhost:5037
    print(adb.start_server())
    # adb.devices()
    adb.device('设备序列号').shell('getprop ro.product.cpu.abi')
    # adb.device('设备序列号').pull('/data/local/tmp/xxxxxxx.apk', r'C:\Users\Desktop\adbProject\xxxxxx.apk')
    # adb.device('设备序列号').push(r'C:\Users\Desktop\adbProject\demo.txt', '/data/local/tmp')
    # adb.device('设备序列号').start_app("com.tencent.mobileqq", "com.tencent.mobileqq.activity.SplashActivity")
    # adb.device('设备序列号').start_app("com.tencent.mobileqq")
    # adb.device('设备序列号').stop_app("com.tencent.mobileqq")
    # adb.device('设备序列号').clear_app("com.tencent.mobileqq")
    # adb.device('设备序列号').install(r"C:\Users\Desktop\adbProject\xxx.apk")
    # adb.device('设备序列号').uninstall("com.tencent.mobileqq")
    # adb.kill_server()