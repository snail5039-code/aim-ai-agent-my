from abc import ABC, abstractmethod
from protocol import Protocol

class Device(ABC):
    def __init__(self, name : str, company : str, protocol : Protocol):
        self.name : str = name
        self.company : str = company
        self.protocol : Protocol = protocol

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
    def __init__(self, name, company, protocol):
        super().__init__(name, company, protocol)
        self.status = False

    def run(self):
        if self.status:
            print("전등 이미 켜져있음")
        else :
            self.status = True
            print("전등 킴!")
    
    def check_status(self):
        if self.status:
            print("전등 켜져있음")
        else :
            print("전등 꺼져있음")

    def stop(self):
        if not self.status:
            print("전등 이미 꺼져있음")
        else :
            self.status = False
            print("전등 끔!!")

class AirConditioner(Device):
    def __init__(self, name, company, protocol):
        super().__init__(name, company, protocol)
        self.status = False
        
    def run(self):
        if self.status:
            print("에어컨 이미 켜져있음")
        else :
            self.status = True
            print("에어컨 킴!")
    
    def check_status(self):
        if self.status:
            print("에어컨 켜져있음")
        else :
            print("에어컨 꺼져있음")

    def stop(self):
        if not self.status:
            print("에어컨 이미 꺼져있음")
        else :
            self.status = False
            print("에어컨 끔!!")