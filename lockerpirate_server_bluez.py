from bluez_peripheral.util import Adapter, get_message_bus
from bluez_peripheral.advert import Advertisement
from bluez_peripheral.agent import NoIoAgent
from bluez_peripheral.gatt.service import Service
from bluez_peripheral.gatt.characteristic import characteristic, CharacteristicFlags as CharFlags
import asyncio
import struct
import os

class LockerService(Service):
    def __init__(self):
        super().__init__("5e400001-b5a3-f393-e0a9-e50e24dcca9e", True)


    @characteristic("5e400002-b5a3-f393-e0a9-e50e24dcca9e", CharFlags.WRITE)
    def char2(self, options):
        pass

    @char2.setter
    def char2(self, value, options):
        print("Got a WRITE to char2")
        print("Value: " + value.hex())
        #self._some_value = value

        val1to30 = value.hex()[0:30]
        val31to34 = value.hex()[30:34] #random
        val35to36 = value.hex()[34:36] # In NOTIFY I need to do -6
        val37to68 = value.hex()[36:68]
        val69to76 = value.hex()[68:76] #random

        print(" val1to30: "+val1to30)
        print("val31to34: "+val31to34)
        print("val35to36: "+val35to36)
        print("val37to68: "+val37to68)
        print("val69to76: "+val69to76)

        valControl = hex(int(val35to36, 16) - int("06", 16))

        valToindicate = "117d" + val1to30[4:] + val31to34 + valControl[2:] + "6164586ba361610261620161675860" + "b436d644a4c864808a249a6bb89b6fa08ed59fe7a99cef276c64377eeac91dabaa3d595927135050461549c38f05fb2023a136c76fce300f36be8f7247c970de6f5e4183cfc89552ad852822f92f06384cfa6997e627f0de595dee85c5f4aaa9"
        # Test Nullify open command. Did NOT work!
        #valToindicate = "117d" + val1to30[4:] + val31to34 + valControl[2:] + "6164586ba361610261620161675860" + "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000" 

        #testing fuzzing the open command
        for x in range(1):
                random60 = os.urandom(96).hex()
                valToindicate = "117d" + val1to30[4:] + val31to34 + valControl[2:] + "6164586ba361610261620161675800" + random60
                self.char3.changed(bytes(bytearray.fromhex(valToindicate)))

        print("done fuzzing")
        #valToindicate = "117d0000a461610161620161631a6504e6036164586ba36161026162016167586097d581e369f02fbff2594737d858aa42cd22b4da3ae1e028c8b06fb7c4f53dddce7295df1543bcad95a479713c90c8717d5d4efab926c0f760a84626718e284b7ecab23f6be16fa58e410ab0cd1b8d734dd56854ed49a0577b6a473d3d2e3117"
        #print("char3 INDICATES this value: " + valToindicate)
        #self.char3.changed(bytes(bytearray.fromhex(valToindicate)))


    @characteristic("5e400003-b5a3-f393-e0a9-e50e24dcca9e", CharFlags.INDICATE)
    def char3(self, options):
        pass


    @characteristic("5e400004-b5a3-f393-e0a9-e50e24dcca9e", CharFlags.READ)
    def char4(self, options):
        print("Got a READ to char4")
        print("Sending value 0x0502")
        return bytes([0x05, 0x02]) # Return default value for all lockers


async def main():

    bus = await get_message_bus()

    service = LockerService()
    await service.register(bus)

    agent = NoIoAgent()
    await agent.register(bus)

    adapter = await Adapter.get_first(bus)

    # Start an advert that will last for 60 seconds.
    print("Start advertising...")
    advert = Advertisement("Amazon Locker", ["180D"], 0x0171, 60, manufacturerData={369: bytes([0x00, 0x11, 0x01, 0x00, 0x01, 0x01, 0x82, 0xa3, 0x25, 0xbe, 0xe7, 0x00])}) # Locker specific
    await advert.register(bus, adapter)

    while True:

        await asyncio.sleep(5)

    await bus.wait_for_disconnect()

if __name__ == "__main__":
    asyncio.run(main())