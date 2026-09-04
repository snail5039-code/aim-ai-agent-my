from device import Device, SmartLight, AirConditioner
from protocol import Protocol, ZigbeeProtocol, WiFiProtocol, BluetoothProtocol
from smartHub import SmartHub


zigbee = ZigbeeProtocol()
wifi = WiFiProtocol()
bluetooth = BluetoothProtocol()

sh = SmartHub("허브", zigbee)

light = SmartLight("전등임", "샤오미??", zigbee)

sh.register_device(light)

sh.run_all()

