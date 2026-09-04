from abc import ABC, abstractmethod

class Protocol(ABC):
    @abstractmethod
    def start_connection(self):
        pass

class WiFiProtocol(Protocol):
    def start_connection(self):
        print("WiFi 연결")

class ZigbeeProtocol(Protocol):
    def start_connection(self):
        print("Zigbee 연결")

class BluetoothProtocol(Protocol):
    def start_connection(self):
        print("블루투스 연결")