import abc
import asyncio
import os
import socket
import subprocess
import time
from shutil import which

from adb_core import AdbClient


class AbstractDevice(abc.ABC):

    @abc.abstractmethod
    def async_server_kill(self):
        pass

    @abc.abstractmethod
    def async_devices(self):
        pass

    @abc.abstractmethod
    def async_shell(self, cmd, serial):
        pass

    @abc.abstractmethod
    def async_pull(self, src, dst, serial):
        pass

    @abc.abstractmethod
    def async_push(self, src, dst, serial):
        pass

    @abc.abstractmethod
    def async_stat(self, src, serial):
        pass


def check_server(host: str, port: int) -> bool:
    s = socket.socket()
    try:
        s.settimeout(.2)
        s.connect((host, port))
        return True
    except:
        return False
    finally:
        s.close()


class AdbManager(AbstractDevice):
    def __init__(self, adb_host, adb_port):
        super().__init__(adb_host, adb_port)
        self._device = None


    @classmethod
    def __loop(cls, args):
        return asyncio.run(args)

    def device(self, device):
        self._device = device
        return self

    @staticmethod
    def start_server():  # start adb server
        if check_server("127.0.0.1", 5037) is False:
            exe = which("adb")
            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            subprocess.run([exe, "start-server"], timeout=20.0, creationflags=flags)
            start_time = time.time()
            while 1:
                if check_server("127.0.0.1", 5037):
                    return True
                if int(time.time()-start_time) == 30:
                    return False
        return True

    def kill_server(self):  # kill adb server
        info = self.__loop(self.async_server_kill())
        print(info)

    def devices(self):  # adb device
        info = self.__loop(self.async_devices())
        print(info)

    def shell(self, cmd):  # adb device
        info = self.__loop(self.async_shell(cmd, self._device))
        print(info)

    def pull(self, src, dst):   # adb pull
        # TODO:没有封装pull文件夹
        info = self.__loop(self.async_pull(src, dst, self._device))
        print(info)

    def push(self, src, dst):   # adb push
        # TODO:没有封装push文件夹
        info = self.__loop(self.async_push(src, dst, self._device))
        return info

    def stat(self, path):
        info = self.__loop(self.async_stat(path, self._device))
        return info

    def start_app(self, package_name: str, activity: str = None):  # start app
        if activity:
            command = ["am", "start", "-n", package_name + "/" + activity]
        else:
            command = ["monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1", ]
        self.shell(command)

    def stop_app(self, package_name: str):  # stop app
        command = ["am", "force-stop", package_name]
        self.shell(command)

    def clear_app(self, package_name: str):  # clear app
        self.shell(["pm", "clear", package_name])

    def install(self, path):  # install app
        info = self.push(path, '/data/local/tmp')
        if info[0] == info[1].size:
            fileinfo = self.stat(info[2])
            print(fileinfo)
            # print(info[2])

    def uninstall(self, package_name: str):  # uninstall app
        self.shell(["pm", "uninstall", package_name])

    def list_packages(self):
        self.shell(["pm", "list", "packages"])


class AdbDevice(AdbClient, AdbManager):
    def __init__(self, adb_host, adb_port,):
        AdbClient.__init__(self, adb_host, adb_port)
