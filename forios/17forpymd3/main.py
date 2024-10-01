import time

from pymd3_manager import IOSDevice


if __name__ == '__main__':
    # TODO：代码一次性的， 只能在一个进程运行。报错不用管， 没处理， 只看功能实现没有
    #  主要为了展示ios17的通信原理，以及对pymobiledevice3库api的二次封装，仅参考学习
    ios_device = IOSDevice()
    # 输入uuid
    uuid = '00008110-0016454102E3801E'
    # 创建通道
    ios_device.dev(uuid).create_t()
    print('休息5s等待与设备创建通信通道')
    time.sleep(5)
    print(ios_device.tunnel_address)
    if ios_device.tunnel_address.get(uuid):
        ios_device.dev(uuid).running_t(ios_device.tunnel_address.get(uuid))
        ios_device.dev(uuid).con_t()
        print('休息5s等待创建服务通道')
        time.sleep(5)
        ios_device.dev(uuid).run_app("com.apple.store.Jolly") # 打开app store
        time.sleep(3)
        ios_device.dev(uuid).end_app("com.apple.store.Jolly") # 关闭app store