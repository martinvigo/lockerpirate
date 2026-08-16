import logging
import asyncio
import threading
import sys
from typing import Any, Dict, Union

from bless import (  # type: ignore
        BlessServer,
        BlessGATTCharacteristic,
        GATTCharacteristicProperties,
        GATTAttributePermissions
        )

#from bleak import BleakAdvertisement, BleakScanner

from CoreBluetooth import (  # type: ignore
    CBService,
    CBCentral,
    CBATTRequest,
    CBCharacteristic,
    CBMutableService,
    CBPeripheralManager,
    CBATTErrorSuccess,
    CBManagerStateUnknown,
    CBManagerStateResetting,
    CBManagerStateUnsupported,
    CBManagerStateUnauthorized,
    CBManagerStatePoweredOff,
    CBManagerStatePoweredOn,
    CBAdvertisementDataLocalNameKey,
    CBAdvertisementDataServiceUUIDsKey,
    CBAdvertisementDataManufacturerDataKey,
)

# Set up global vars
step1 = False
step2 = False
step3 = False
step4 = False
step5 = False


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(name=__name__)

trigger: Union[asyncio.Event, threading.Event]
if sys.platform in ["darwin", "win32"]:
    trigger = threading.Event()
else:
    trigger = asyncio.Event()


def read_request(
        characteristic: BlessGATTCharacteristic,
        **kwargs
        ) -> bytearray:
    if(characteristic.uuid == "5e400004-b5a3-f393-e0a9-e50e24dcca9e"):
        characteristic.value = bytearray.fromhex("0502")
    elif(characteristic.uuid == "5e400002-b5a3-f393-e0a9-e50e24dcca9e"):
        characteristic.value = bytearray.fromhex("10220000a461610161620161631a6502ff32616451a46161016162016172f5616544d4178530")
    else:
        print("NO UUID FOUND!!!!!!!!!!!!")
    logger.debug(f"Reading {characteristic.value}")
    trigger.set()
    return characteristic.value


def write_request(
        characteristic: BlessGATTCharacteristic,
        value: Any,
        **kwargs
        ):
    characteristic.value = value
    logger.debug(f"Char value set to {characteristic.value} in characteristic {characteristic.uuid}")
    trigger.set()

async def run_mine(loop):
    trigger.clear()

    # Instantiate the server
    gatt: Dict = {
            "5e400001-b5a3-f393-e0a9-e50e24dcca9e": {
                "5e400002-b5a3-f393-e0a9-e50e24dcca9e": {
                    "Properties": GATTCharacteristicProperties.write,
                    "Permissions": GATTAttributePermissions.writeable,
                    "Value": None
                },
                "5e400003-b5a3-f393-e0a9-e50e24dcca9e": {
                    "Properties": GATTCharacteristicProperties.indicate,
                    "Permissions": None,
                    "Value": None
                },
                "5e400004-b5a3-f393-e0a9-e50e24dcca9e": {
                    "Properties": GATTCharacteristicProperties.read,
                    "Permissions": GATTAttributePermissions.readable,
                    "Value": None
                }
            }
        }
    

    # Set up server
    my_service_name = "Amazon.con Services LLC"
    server = BlessServer(name=my_service_name, loop=loop, ) #, adapter="hci0"
    
    server.read_request_func = read_request
    server.write_request_func = write_request

    # Define your manufacturer data (replace with your own values)
    manufacturer_data = bytes([0x4C, 0x00, 0x02, 0x15, 0xE2, 0x0A, 0x39, 0xF4, 0x53, 0xF5, 0x4B, 0xC3, 0xA1, 0x2F, 0x17, 0xD1, 0xAD, 0x07, 0xA9, 0x61, 0x00, 0x00, 0x00, 0x00, 0x2A])
    advertisement_data = {
            CBAdvertisementDataLocalNameKey: "AAAAAAAAAAAAAAAAAAAAAA",
        }
    # # Create an advertisement object
    # advertisement = BleakAdvertisement(advertisement_data=advertisement_data)

    # # Start advertising
    # scanner = BleakScanner()
    # scanner.register_detection_callback(lambda device, advertisement_data: print(f"Detected: {device.address}"))
    # await scanner.start()
    # await scanner.set_scanning_filter(advertisement)
    # await asyncio.sleep(10)  # Adjust timeout as needed

    # # Stop advertising
    # await scanner.stop()

    # print("Advertisement sent successfully!")

    manufacturer_specific = bytearray.fromhex("0fff710100110100010183a225bde700")
    manufacturer_specific = bytearray.fromhex("0fff0000000000000000000000000000")
    #manufacturer_specific = {76: [16, 5, 7, 24, 186, 175, 161]}
    advertisement_data = {
            CBAdvertisementDataLocalNameKey: "BBBB",
            CBAdvertisementDataManufacturerDataKey: manufacturer_specific,
        }
    logger.debug("Advertisement Data: {}".format(advertisement_data))
    try:
        await server.peripheral_manager_delegate.start_advertising(advertisement_data)
    except TimeoutError:
        # If advertising fails as a result of bluetooth module power
        # cycling or advertisement failure, attempt to start again
        await self.start()
        print("ERRORRRRRR")

    logger.debug("Advertising...")
    trigger.wait()


    # Start server
    await server.add_gatt(gatt)
    await server.start()

    # Wait for the 0502 red request
    print("Step 1: Client sends a read request to 5e400004 and server answers with 0x0502")
    trigger.wait()
    print("Done with step 1. Next!")

    print("Step 2: Client sends a write request to 5e400002 with payload 10220000a461610161620161631a6502ff32616451a46161016162016172f5616544d4178530")
    trigger.clear()
    trigger.wait()
    print("Done with step 2. Next!")

    print("Step 3: Client sends a read request to 5e400004 and server answers with 0x0502")
    trigger.clear()
    trigger.wait()
    print("Done with step 3. Next!")

    print("Step 4: Client sends a write request to 5e400002 with payload 10910100a461610161620161631a6502ff38616459017ea861610361620161681864616958a43076301006072a8648ce3d020106052b8104002203620004572bbfa9d2d0c691efa36e36008f1ac669d88d4118f15d8f5a1d1d7da366c800ef40912c106614a5f65ee32dd8cc5c6f794a936b9602581b7c75048578579eb2d09e0c08c4b2d7661c902ce2a738fa3d81ed214101c80b4bdb63c3a63e2dcecf33c2f9ede15a31076a056df6b96dafd1d049acb2c0f8f4bf285a94fa718610b877341f31260d6cfc62cc0796616a582c627491fb3bc2a4693306030caa44e255945d253e3661b6ec92d2455b65dd5864cd51f85be9126d2423028e26616b4465045093616c582432393734343838662d393637622d346636342d393830392d383461303934633839653565616d586830660231008be708303b2196dbe32a4b0b21ea1a5bcca8b4d7526180575083e8b79bf68d644e7a3f027e86530b252febacd3ef3d1b023100ab34b9751fb727b0363233cc528a89d1863983f74bedec582b970c1067cc41598a6942dcbebe6f32fa37d6a755231eb1")
    trigger.clear()
    trigger.wait()
    print("Done with step 4. Next!")

    print("Step 5: Client sends a write request to 5e400002 with payload 103d0000a461610161620161631a6502ff3f6164582ba361610661620161665820ef3dcfcc08db08a90174c091e7a11b9f6ada0da70bbc40302127a1af368dcfa4")
    trigger.clear()
    trigger.wait()
    print("Done with step 5. Next!")

    
    # Shutdown server
    await asyncio.sleep(5)
    await server.stop()




async def advertise_manufacturer_data():
    # Define your manufacturer data (replace with your own values)
    manufacturer_data = bytes([0x4C, 0x00, 0x02, 0x15, 0xE2, 0x0A, 0x39, 0xF4, 0x73, 0xF5, 0x2B, 0xC4, 0xA1, 0x2F, 0x18, 0xD1, 0xAD, 0x07, 0xA8, 0x61, 0x00, 0x00, 0x00, 0x00, 0x2A])

    # Create an advertisement object
    advertisement = BleakAdvertisement(manufacturer_data=manufacturer_data)

    # Start advertising
    scanner = BleakScanner()
    scanner.register_detection_callback(lambda device, advertisement_data: print(f"Detected: {device.address}"))
    await scanner.start()
    await scanner.set_scanning_filter(advertisement)
    await asyncio.sleep(10)  # Adjust timeout as needed

    # Stop advertising
    await scanner.stop()

    print("Advertisement sent successfully!")









async def run(loop):
    trigger.clear()

    # Instantiate the server
    gatt: Dict = {
            "A07498CA-AD5B-474E-940D-16F1FBE7E8CD": {
                "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B": {
                    "Properties": (GATTCharacteristicProperties.read |
                                   GATTCharacteristicProperties.write |
                                   GATTCharacteristicProperties.indicate),
                    "Permissions": (GATTAttributePermissions.readable |
                                    GATTAttributePermissions.writeable),
                    "Value": None
                    }
                },
            "5c339364-c7be-4f23-b666-a8ff73a6a86a": {
                "bfc0c92f-317d-4ba9-976b-cc11ce77b4ca": {
                    "Properties": GATTCharacteristicProperties.read,
                    "Permissions": GATTAttributePermissions.readable,
                    "Value": bytearray(b'\x69')
                }
            }
        }
    my_service_name = "Amazon Locker"
    server = BlessServer(name=my_service_name, loop=loop)
    server.read_request_func = read_request
    server.write_request_func = write_request

    await server.add_gatt(gatt)
    await server.start()
    logger.debug(server.get_characteristic(
        "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B"))
    logger.debug("Advertising")
    logger.info("Write '0xF' to the advertised characteristic: " +
                "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B")
    trigger.wait()
    await asyncio.sleep(2)
    logger.debug("Updating")
    server.get_characteristic("51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B").value = (
            bytearray(b"i")
            )
    server.update_value(
            "A07498CA-AD5B-474E-940D-16F1FBE7E8CD",
            "51FF12BB-3ED8-46E5-B4F9-D64E2FEC021B"
            )
    await asyncio.sleep(5)
    await server.stop()


# START
loop = asyncio.get_event_loop()
loop.run_until_complete(run_mine(loop))

# loop = asyncio.get_event_loop()
# loop.run_until_complete(advertise_manufacturer_data())
# END
