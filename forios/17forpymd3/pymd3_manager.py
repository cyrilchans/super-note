from base_packing import PackingPymd3


class TestDemo:
    def device(self, uuid):
        pass

    def start_tunnel(self, address):
        pass

    def con(self):
        pass

    def create_tunnel(self):
        pass

    def start_app(self, bundle_id: str):
        pass

    def close_app(self, bundle_id: str, pid: int = None):
        pass

    def install_app(self, ipa_path):
        pass

    def uninstall_app(self, bundle_id: str):
        pass


class Pymd3Func(TestDemo):
    def dev(self, device):
        self.device(device)
        return self

    def running_t(self, address):
        self.start_tunnel(address)

    def con_t(self):
        self.con()

    def create_t(self):
        self.create_tunnel()

    def run_app(self, bundle_id):
        self.start_app(bundle_id)

    def end_app(self, bundle_id, pid=None):
        self.close_app(bundle_id, pid)

    def install(self, ipa_path):
        self.install_app(ipa_path)

    def uninstall(self, bundle_id):
        self.uninstall_app(bundle_id)



























































class IOSDevice(PackingPymd3, Pymd3Func):
    def __init__(self):
        PackingPymd3.__init__(self)
