from abc import ABC, abstractmethod

class SmartHub:

    def __init__(self, name :str, protocol :Protocol, devices :list[Device]):
        self.name :str = name
        self.protocol :Protocol = protocol
        self.devices :list[Device]= devices


    def register_device(self):
        pass

    def run_all(self):
        pass

    def stop_all(self):
        pass

class Protocol:
    pass

class Device(ABC):

    def __init__(self, name :str, compnay :str, protocol :Protocol):
        self.name :str = name
        self.company :str = compnay
        self.protocol :Protocol = protocol

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def check_status(self):
        pass

    @abstractmethod
    def stop(self):
        pass




class SmartLight(Device):

    def run(self):
        pass

class AirConditioner(Device):

    def run(self):
        pass

