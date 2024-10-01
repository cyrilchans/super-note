"""
    直接使用pymobiledevice3 usbmux实现与ios17设备的通信服务
    pymobiledevice3 == 4.13.12
"""
import asyncio
import threading
import typing

from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.remote.remote_service_discovery import RemoteServiceDiscoveryService
from pymobiledevice3.remote.tunnel_service import RemotePairingProtocol, CoreDeviceTunnelProxy, RemotePairingTcpTunnel
from pymobiledevice3.services.dvt.dvt_secure_socket_proxy import DvtSecureSocketProxyService
from pymobiledevice3.services.dvt.instruments.device_info import DeviceInfo
from pymobiledevice3.services.dvt.instruments.process_control import ProcessControl
from pymobiledevice3.services.installation_proxy import InstallationProxyService
from pymobiledevice3.usbmux import list_devices


class PackingPymd3:
    def __init__(self):
        self._tun_read_task = None
        self.service_provider = None
        self._rsd = None
        self.tunnel_address: typing.Dict[str, tuple] = {}
        self.stop_event = asyncio.Event()
        self._uuid = str()

    def device(self, uuid):
        self._uuid = uuid
        return self

    async def start_tunnel_task(
            self, protocol_handler: typing.Union[RemotePairingProtocol, CoreDeviceTunnelProxy]) -> None:
        ser = await self.service_provider.aio_start_lockdown_service(protocol_handler.SERVICE_NAME)
        tunnel = RemotePairingTcpTunnel(ser.reader, ser.writer)
        handshake_response = await tunnel.request_tunnel_establish()
        tunnel.start_tunnel(handshake_response['clientParameters']['address'],
                            handshake_response['clientParameters']['mtu'])
        print(handshake_response['serverAddress'], handshake_response['serverRSDPort'])
        try:
            self.tunnel_address[self._uuid] = (handshake_response['serverAddress'], handshake_response['serverRSDPort'])
            while not self.stop_event.is_set():
                await asyncio.sleep(1)
        finally:
            await tunnel.stop_tunnel()

    async def connect_tunnel_for_usbmux(self):
        get_local_devices = list_devices()
        exists_device = [i.serial for i in get_local_devices if i.serial == self._uuid and i.is_usb]
        if not exists_device:
            print('未搜到此设备， 检查设备是否连接')
            return
        self.service_provider = create_using_usbmux(self._uuid)
        service = CoreDeviceTunnelProxy(create_using_usbmux(self._uuid))
        self._tun_read_task = asyncio.create_task(self.start_tunnel_task(service), name=f'tun-read-{self._uuid}')
        await self._tun_read_task

    async def connect(self):
        await self._rsd.connect()

    def con(self):
        asyncio.run(self.connect())

    def start_tunnel(self, address):
        self._rsd = RemoteServiceDiscoveryService(address)
        return self

    def start_app(self, bundle_id: str) -> None:
        with DvtSecureSocketProxyService(lockdown=self._rsd) as dvt:
            app_manager = DeviceProcessControl(dvt)
            app_manager.start_app(bundle_id)

    def close_app(self, bundle_id: str, pid: int = None) -> None:
        if pid is None:
            with DvtSecureSocketProxyService(lockdown=self._rsd) as dvt:
                app_device_manager = DeviceInfoManager(dvt)
                pid = app_device_manager.find_bundle(bundle_id)
                print(f'halo,{pid}')
        if pid is None:
            print('没找到指定应用的进程，进程已被杀死')
            return
        with DvtSecureSocketProxyService(lockdown=self._rsd) as dvt:
            app_process_manager = DeviceProcessControl(dvt)
            app_process_manager.close_app(pid)

    def install_app(self, ipa_path):
        InstallationProxyService(lockdown=self._rsd).install_from_local(ipa_path)

    def uninstall_app(self, bundle_id: str):
        InstallationProxyService(lockdown=self._rsd).uninstall(bundle_id)

    def run_routine(self):
        asyncio.run(self.connect_tunnel_for_usbmux())

    def create_tunnel(self):
        t1 = threading.Thread(target=self.run_routine)
        t1.start()


class DeviceProcessControl(ProcessControl):
    # 继承覆写pymobiledevice3里面的实现
    def __init__(self, dvt: DvtSecureSocketProxyService):
        ProcessControl.__init__(self, dvt)

    def start_app(self, bundle_id: str):
        ProcessControl.launch(self, bundle_id)

    def close_app(self, pid: int):
        super().kill(pid)


class DeviceInfoManager(DeviceInfo):
    def __init__(self, dvt: DvtSecureSocketProxyService):
        DeviceInfo.__init__(self, dvt)

    def proclist(self) -> typing.List[typing.Mapping]:
        """
        就是想重写
        """
        self._channel.runningProcesses()
        result = self._channel.receive_plist()
        assert isinstance(result, list)
        return result

    def find_bundle(self, bundle_id: str):
        process_list = self.proclist()
        for index in process_list:
            if index.get("bundleIdentifier") == bundle_id:
                print('1111')
                return index["pid"]
        return

