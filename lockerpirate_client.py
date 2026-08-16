import asyncio
from bleak import BleakScanner, BleakClient
import binascii
import time
import os

# Identifiers (MacOS hides MAC addresses so we need to look for manufacturerData and retrieve de identifier that way (UUID))
deviceIdentifier = "" #Rpi Mac Address
manufacturerData={369: bytes([0x00, 0x11, 0x01, 0x00, 0x01, 0x01, 0x83, 0xa2, 0x34, 0xbd, 0x27, 0x00])} # Locker Manufacturer ID

# Locker advertised GATT Services
service1 = "5e400001-b5a3-f393-e0a9-e50e24dcca9e"
characteristic2 = "5e400002-b5a3-f393-e0a9-e50e24dcca9e"
characteristic3 = "5e400003-b5a3-f393-e0a9-e50e24dcca9e"
characteristic4 = "5e400004-b5a3-f393-e0a9-e50e24dcca9e"

notificationData = False # The data we get from the locker after each write in form of NOTIFY

async def main():
    global notificationData
    stop_event = asyncio.Event()

    # Callback function for the scanner
    def scanForDevices(foundDevice, advertising_data):
        global deviceIdentifier

        print("A device found!")
        print("Identifier: " + foundDevice.address + 
            ", name: " + str(advertising_data.local_name) + 
            ", RSSI: " + str(advertising_data.rssi) + 
            ", TX Power: " + str(advertising_data.tx_power) + 
            ", MTU: " + str(advertising_data.platform_data[0].mtuLength()) + 
            ", metadataUUID: " + str(advertising_data.service_uuids) + 
            ", metadataManufacturerData: " + str(advertising_data.manufacturer_data) + 
            ", state: " + str(advertising_data.platform_data[0].state()) + 
            ", BDAddress: " + str(advertising_data.platform_data[0].BDAddress()))
        
        if(advertising_data.manufacturer_data == manufacturerData):
            stop_event.set() # Stop scanning
            print("Locker found!!!")
            print("Identifier: " + foundDevice.address + 
              ", name: " + str(advertising_data.local_name) + 
              ", RSSI: " + str(advertising_data.rssi) + 
              ", TX Power: " + str(advertising_data.tx_power) + 
              ", MTU: " + str(advertising_data.platform_data[0].mtuLength()) + 
              ", metadataUUID: " + str(advertising_data.service_uuids) + 
              ", metadataManufacturerData: " + str(advertising_data.manufacturer_data) + 
              ", state: " + str(advertising_data.platform_data[0].state()) + 
              ", BDAddress: " + str(advertising_data.platform_data[0].BDAddress()))
            deviceIdentifier = foundDevice.address
            
            
    # Callback function for processing notifications
    def processNotification(sender, data):
        global notificationData

        notificationData = str(data)
        print("Got NOTIFY with value: " + str(binascii.hexlify(data)))
        stop_event.set() # Stop waiting for notification

    
    async with BleakScanner(scanForDevices) as scanner: # Start scanning
        print("Scanning for the device with ID: " + deviceIdentifier + "...")
        await stop_event.wait()


    # At this point, device was found, let's get the services
    async with BleakClient(deviceIdentifier) as client: # Instanciate a BleakClient object        

        # Step 0: Phone subscribes to NOTIFY for 5e400003
        print("Step 0: Phone subscribes to NOTIFY for 5e400003")
        await client.start_notify(characteristic3, processNotification)
        print("Done with step 0. Next!")


        # Step 1: Send READ request to 5e400004 and get back 0x0502
        print("Step 1: Phone sends a read request to 5e400004 and Locker responds with 0x0502")
        response1 = await client.read_gatt_char(characteristic4)
        print("This is the response I got for Step 1: " + str(response1))
        print("Done with step 1. Next!")


        #################
        ### RUN TESTS ###
        #################
        runtests = True
        if(runtests):
            print("TESSSSTINGGGGGGG!!!!!!!")
            # Step 2: Phone sends write request to 5e400002 with payload similar to: 10220000a461610161620161631a6502ff32616451a46161016162016172f5616544d4178530
            header_byte = "10"
            length1 = "22"
            #length1 = "00" # Did not work
            static_overall1 = "0000"
            static_overall2 = "a461610161620161631a"
            #static_overall2 = "00000000000000000000" # Did not work
            timestamp = str(hex(int(time.time())))[2:]
            #timestamp = "00000000" # Worked!
            static_overall3 = "616451a46161016162016172f5616544"
            #static_overall3 = "616451a46161016162016172f5610044" # Did not work
            unknown1 = "99999999"   
            #unknown1 = "00000000" # Worked!
            
            packet2Payload = header_byte + length1 + static_overall1 + static_overall2 + timestamp + static_overall3 + unknown1
            packet2Payload = "10220000a461610161620161631a662d0bf0616451a46161016162016172f56165447fed2eb4"
            print("Step 2: Phone sends a WRITE request to 5e400002 with payload " + packet2Payload)
            await client.write_gatt_char(characteristic2, bytearray.fromhex(packet2Payload), response=True)
            print("Done with step 2. Next!")

            print("Waiting for NOTIFY after Step 2...")
            stop_event.clear()
            await stop_event.wait()

            # Step 3: Phone sends a WRITE request to 5e400002 with payload similar to: 10910100a461610161620161631a6502ff38616459017ea861610361620161681864616958a43076301006072a8648ce3d020106052b8104002203620004572bbfa9d2d0c691efa36e36008f1ac669d88d4118f15d8f5a1d1d7da366c800ef40912c106614a5f65ee32dd8cc5c6f794a936b9602581b7c75048578579eb2d09e0c08c4b2d7661c902ce2a738fa3d81ed214101c80b4bdb63c3a63e2dcecf33c2f9ede15a31076a056df6b96dafd1d049acb2c0f8f4bf285a94fa718610b877341f31260d6cfc62cc0796616a582c627491fb3bc2a4693306030caa44e255945d253e3661b6ec92d2455b65dd5864cd51f85be9126d2423028e26616b4465045093616c582432393734343838662d393637622d346636342d393830392d383461303934633839653565616d586830660231008be708303b2196dbe32a4b0b21ea1a5bcca8b4d7526180575083e8b79bf68d644e7a3f027e86530b252febacd3ef3d1b023100ab34b9751fb727b0363233cc528a89d1863983f74bedec582b970c1067cc41598a6942dcbebe6f32fa37d6a755231eb1
            header_byte = "10"
            #header_byte = "00" # Did not work
            length1 = "8f" # 91, 90 y 8f Because the size of this packet varies
            #length1 = "8f" # Did not work
            static_overall1 = "0100"
            #static_overall1 = "0000" # Did not work
            static_overall2 = "a461610161620161631a"
            #static_overall2 = "00000000000000000000" # Did not work
            timestamp = str(hex(int(time.time())))[2:]
            #timestamp = "00000000" # Worked!
            static_overall3 = "616459"
            #static_overall3 = "000000" # Did not work
            length2 = "017c" # This length I think uses 2 bytes. 017c, 017d y 017e
            #length2 = "0000" # Did not work
            static_overall4 = "a861610361620161681864616958a43076301006072a8648ce3d020106052b8104002203620004" # a8 6161 03 6162 01 6168 1864 6169 58 a4 3076301 00 6072a8648ce3d020106052b8104 00 220362 0004
            #static_overall4 = "000000000000000000000000000000000000000000000000000000000000000000000000000000" # Did not work
            unknown1 = os.urandom(140).hex() # d70ea24462fbce54c5b7b2e90a9c7a9528f3571fd72fbbf4483116d6f8a589a3b221c724a684df7105f23bd07b8ae0f75df819a2c355469f4d93716abd8dd6427f2d0490f08c5a2e8779d1d2670353ba69d7caa8d858b1f7dd77034419a724c8461c3662e6b8d833d494bebb1fc8d0e8ab72c2dd8b190fbc78dd886bdb9d92640fe10475828e7ea90b0a75a4
            #unknown1 = "00"*140 # Worked!
            static_overall5 = "616a582c" # note it includes a size
            #static_overall5 = "00000000" # Did not work
            unknown2 = os.urandom(44).hex() # 2a5c12214ccc63c5d9c8511764bab7b6cf754fdeaf4f447c9040ca69559f3a6148da65f3dc3dea9e2ba87724
            #unknown2 = "00"*44 # Worked!
            static_overall6 = "616b44" # This comes before another timestamp...
            #static_overall6 = "000000" # Did not work
            timestamp2 = str(hex(int(time.time())))[2:] # This timestamp should be a bit in the past respect to the present. TBD how much in the past...
            #timestamp2 = "00000000" # Worked!
            static_overall7 = "616c5824"
            #static_overall7 = "00000000" # Did not work

            #182dd5d8-2200-4845-9a4c-43dd13906465
            #3138326464356438 2D 32323030 2D 34383435 2D 39613463 2D 343364643133393036343635
            uuidPart1 = "3436386330393362"
            uuidPart1 = "3138326464356438" # Worked!
            separator = "2d"
            uuidPart2 = "32393962"
            uuidPart2 = "32323030" # Worked!
            separator = "2d"
            uuidPart3 = "34626335"
            uuidPart3 = "34383435" # Worked!
            separator = "2d"
            uuidPart4 = "62663964"
            uuidPart4 = "39613463" # Worked!
            separator = "2d"
            uuidPart5 = "656465353664663964643437"
            uuidPart5 = "343364643133393036343635" # Worked!
            static_overall8 = "616d" # Note it includes a VARIABLE size next
            #static_overall8 = "0000" # Did not work
            length3 = "5866" # 66, 67 y 68
            #length3 = "0000" # Did not work 
            static_overall9 = "30"
            #static_overall9 = "00" # Worked!
            length4 = "64" # 64, 65 o 66
            #length4 = "00" # Worked!
            static_overall10 = "02"
            #static_overall10 = "00" # Worked!
            length5 = "30" # 30 si la anterior longitud es 64 o 31 si es 65 o 66
            #length5 = "00" # Worked!
            unknown3 = "5c" # He visto varios casos de 00, pero tambien 5c, 2f, 41 y 49
            #unknown3 = "00" # Worked!
            unknown4 =  os.urandom(97).hex() # variable el length. 3834f1712647bf14825d99bca8164add1229173ec2a41275275d76040e9b6ffdfd99766878c4700af25b04d1f1246b02300cc21024d996a580b02f1fada29ebc9b4cb7a6482d63da0b860fc4de427c34a754c0baceb3f7153bcc07205ea92c79ae
            #unknown4 = "00"*97 # Worked!

            packet4Payload = header_byte + length1 + static_overall1 + static_overall2 + timestamp + static_overall3 + length2 + static_overall4 + unknown1 + static_overall5 + unknown2 + static_overall6 + timestamp2 + static_overall7 + uuidPart1 + separator + uuidPart2 + separator + uuidPart3 + separator + uuidPart4 + separator + uuidPart5 + static_overall8 + length3 + static_overall9 + length4 + static_overall10 + length5 + unknown3 + unknown4
            packet4Payload = "10900100a461610161620161631a662d0bf3616459017da861610361620161681864616958a43076301006072a8648ce3d020106052b8104002203620004e508f4facb0419cea15869fcc21ffc72173d61e84f14ac026a54db7f19e22b15283da7c2d28a052651c5ac442bffa91a3946bf6bab3bff4c5d4bc490b4331af50b32b40cdc829191e3e579a221832702455f1d56c27f19a7b61512192b1fa49021f29b0bd39b7b888facd16d7f4ed0dcca9aee3eb05e713df818ab4605eb77013e2b9f0517293d58759932d9616a582ccd74fed3ba9c12549a32c14e6a67c90e1fce0986670c9df3e22840fd455a5ec6ec7c2e1d4909b95f4bb0eacd616b446633a254616c582466633166653762632d383061322d343536622d386636322d653763643836353738353666616d58673065023100c072d2af719af1767d34a57137aac34f3ae53fbf5d81a264a37b9481c734d1621146d0bab6485460d017e4f38fd8eeea02303abad7566b2609673cdd56af315e4639f864e2348c8b8c2c192f5b641165453a23c91cc52ff33a2a4dde9d3bbf03a109"
            print("Step 3: Phone sends a WRITE request to 5e400002 with payload " + packet4Payload)
            await client.write_gatt_char(characteristic2, bytearray.fromhex(packet4Payload), response=True)
            print("Done with step 3. Next!")

            print("Waiting for NOTIFY after Step 3...")
            stop_event.clear()
            await stop_event.wait()

            # Step 4: Phone sends a WRITE request to 5e400002 with payload similar to: 10680000a461610261620161631a65493b7261645856a2616f582032ba11a1c05f8ad3cf9186989899450345c4c1171c3a2a6e8654ae8cedccfa916170582d3d24aae455f37dc9591e39d29bf7948b7c4c4a11ab47557a53ea58707ea6e180f346e25ff1855e92dcfdab150c
            header_byte = "10"
            length1 = "68"
            static_overall1 = "0000"
            static_overall2 = "a461610261620161631a"
            timestamp = str(hex(int(time.time())))[2:]
            #timestamp = "00000000" # ???
            static_overall3 = "6164"
            length2 = "5857"
            static_overall4 = "a2616f"
            length3 = "5820"
            unknown1 = os.urandom(32).hex() # 32ba11a1c05f8ad3cf9186989899450345c4c1171c3a2a6e8654ae8cedccfa91
            #unknown1 = "00"*32 # ???
            static_overall5 = "6170"
            #length4 = "582d"
            length4 = "582e" # For testing the payload
            unknown2 = os.urandom(45).hex() # 3d24aae455f37dc9591e39d29bf7948b7c4c4a11ab47557a53ea58707ea6e180f346e25ff1855e92dcfdab150c
            #unknown2 = "00"*45 # ???
            unknown2 = "90fab97a576308ee670962b8ae71b424c1d8b5862ea03aed3de14634899be108bb24aa7e52081869e03f99e8de53" # ???

            packet6Payload = header_byte + length1 + static_overall1 + static_overall2 + timestamp + static_overall3 + length2 + static_overall4 + length3 + unknown1 +static_overall5 + length4 + unknown2
            print("Step 4: Client sends a write request to 5e400002 with payload " + packet6Payload)
            await client.write_gatt_char(characteristic2, bytearray.fromhex(packet6Payload), response=True)
            print("Done with step 4. Next!")

            print("Waiting for NOTIFY after Step 4...")
            stop_event.clear()
            await stop_event.wait()

            return 0
        #####################
        ### END RUN TESTS ###
        #####################


        # Step 2: Phone sends write request to 5e400002 with payload similar to: 10220000a461610161620161631a6502ff32616451a46161016162016172f5616544d4178530
        # 10 22 0000 a461610161620161631a 66034fc0 6164 51      a4 6161 01 6162 01 6172 f5 6165 44 4e6d 7a6c
        header_byte = "10"
        length1 = "22"
        static_overall1 = "0000"
        static_overall2 = "a461610161620161631a"
        timestamp = str(hex(int(time.time())))[2:]
        static_overall3 = "616451a46161016162016172f5616544"
        unknown1 = "99999999"

        packet2Payload = header_byte + length1 + static_overall1 + static_overall2 + timestamp + static_overall3 + unknown1
        print("Step 2: Phone sends a WRITE request to 5e400002 with payload " + packet2Payload)
        await client.write_gatt_char(characteristic2, bytearray.fromhex(packet2Payload), response=True)
        print("Done with step 2. Next!")

        print("Waiting for NOTIFY after Step 2...")
        stop_event.clear()
        await stop_event.wait()

        # Step 3: Phone sends a WRITE request to 5e400002 with payload similar to: 10910100a461610161620161631a6502ff38616459017ea861610361620161681864616958a43076301006072a8648ce3d020106052b8104002203620004572bbfa9d2d0c691efa36e36008f1ac669d88d4118f15d8f5a1d1d7da366c800ef40912c106614a5f65ee32dd8cc5c6f794a936b9602581b7c75048578579eb2d09e0c08c4b2d7661c902ce2a738fa3d81ed214101c80b4bdb63c3a63e2dcecf33c2f9ede15a31076a056df6b96dafd1d049acb2c0f8f4bf285a94fa718610b877341f31260d6cfc62cc0796616a582c627491fb3bc2a4693306030caa44e255945d253e3661b6ec92d2455b65dd5864cd51f85be9126d2423028e26616b4465045093616c582432393734343838662d393637622d346636342d393830392d383461303934633839653565616d586830660231008be708303b2196dbe32a4b0b21ea1a5bcca8b4d7526180575083e8b79bf68d644e7a3f027e86530b252febacd3ef3d1b023100ab34b9751fb727b0363233cc528a89d1863983f74bedec582b970c1067cc41598a6942dcbebe6f32fa37d6a755231eb1
        # 10 8f 0100 a461610161620161631 a66034fc2 6164 59 017c a8 6161 03 6162 01 6168 1864 6169 58 a4 3076301 00 6072a8648ce3d020106052b8104 00 220362 0004 d70ea24462fbce54c5b7b2e90a9c7a9528f3571fd72fbbf4483116d6f8a589a3b221c724a684df7105f23bd07b8ae0f75df819a2c355469f4d93716abd8dd6427f2d0490f08c5a2e8779d1d2670353ba69d7caa8d858b1f7dd77034419a724c8461c3662e6b8d833d494bebb1fc8d0e8ab72c2dd8b190fbc78dd886bdb9d92640fe10475828e7ea90b0a75a4 616a 58 2c 2a5c12214ccc63c5d9c8511764bab7b6cf754fdeaf4f447c9040ca69559f3a6148da65f3dc3dea9e2ba87724 616b 44 6609e73d 616c 58 24 3436386330393362 2d 32393962 2d 34626335 2d 62663964 2d 656465353664663964643437 616d 58 66 30 64 02 30 5c 3834f1712647bf14825d99bca8164add1229173ec2a41275275d76040e9b6ffdfd99766878c4700af25b04d1f1246b02300cc21024d996a580b02f1fada29ebc9b4cb7a6482d63da0b860fc4de427c34a754c0baceb3f7153bcc07205ea92c79ae
        header_byte = "10"
        length1 = "8f" # 91, 90 y 8f Because the size of this packet varies
        static_overall1 = "0100"
        static_overall2 = "a461610161620161631a"
        timestamp = str(hex(int(time.time())))[2:]
        static_overall3 = "616459"
        length2 = "017c" # This length I think uses 2 bytes. 017c, 017d y 017e
        static_overall4 = "a861610361620161681864616958a43076301006072a8648ce3d020106052b8104002203620004" # a8 6161 03 6162 01 6168 1864 6169 58 a4 3076301 00 6072a8648ce3d020106052b8104 00 220362 0004
        unknown1 = os.urandom(140).hex() # d70ea24462fbce54c5b7b2e90a9c7a9528f3571fd72fbbf4483116d6f8a589a3b221c724a684df7105f23bd07b8ae0f75df819a2c355469f4d93716abd8dd6427f2d0490f08c5a2e8779d1d2670353ba69d7caa8d858b1f7dd77034419a724c8461c3662e6b8d833d494bebb1fc8d0e8ab72c2dd8b190fbc78dd886bdb9d92640fe10475828e7ea90b0a75a4
        static_overall5 = "616a582c" # note it includes a size
        unknown2 = os.urandom(44).hex() # 2a5c12214ccc63c5d9c8511764bab7b6cf754fdeaf4f447c9040ca69559f3a6148da65f3dc3dea9e2ba87724
        static_overall6 = "616b44" # This comes before another timestamp...
        timestamp2 = str(hex(int(time.time())))[2:] # This timestamp should be a bit in the past respect to the present. TBD how much in the past...
        static_overall7 = "616c5824"
        uuidPart1 = "3436386330393362"
        separator = "2d"
        uuidPart2 = "32393962"
        separator = "2d"
        uuidPart3 = "34626335"
        separator = "2d"
        uuidPart4 = "62663964"
        separator = "2d"
        uuidPart5 = "656465353664663964643437"
        static_overall8 = "616d"
        length3 = "5866" # 66, 67 y 68
        static_overall9 = "30"
        length4 = "64" # 64, 65 o 66
        static_overall10 = "02"
        length5 = "30" # 30 si la anterior longitud es 64 o 31 si es 65 o 66
        unknown3 = "5c" # He visto varios casos de 00, pero tambien 5c, 2f, 41 y 49
        unknown4 =  os.urandom(97).hex() # variable el length. 3834f1712647bf14825d99bca8164add1229173ec2a41275275d76040e9b6ffdfd99766878c4700af25b04d1f1246b02300cc21024d996a580b02f1fada29ebc9b4cb7a6482d63da0b860fc4de427c34a754c0baceb3f7153bcc07205ea92c79ae

        packet4Payload = header_byte + length1 + static_overall1 + static_overall2 + timestamp + static_overall3 + length2 + static_overall4 + unknown1 + static_overall5 + unknown2 + static_overall6 + timestamp2 + static_overall7 + uuidPart1 + separator + uuidPart2 + separator + uuidPart3 + separator + uuidPart4 + separator + uuidPart5 + static_overall8 + length3 + static_overall9 + length4 + static_overall10 + length5 + unknown3 + unknown4
        print("Step 3: Phone sends a WRITE request to 5e400002 with payload " + packet4Payload)
        await client.write_gatt_char(characteristic2, bytearray.fromhex(packet4Payload), response=True)
        print("Done with step 3. Next!")

        print("Waiting for NOTIFY after Step 3...")
        stop_event.clear()
        await stop_event.wait()

        # Step 4: Phone sends a WRITE request to 5e400002 with payload similar to: 10680000a461610261620161631a65493b7261645856a2616f582032ba11a1c05f8ad3cf9186989899450345c4c1171c3a2a6e8654ae8cedccfa916170582d3d24aae455f37dc9591e39d29bf7948b7c4c4a11ab47557a53ea58707ea6e180f346e25ff1855e92dcfdab150c
        # 10 68 0000 a461610261620161631a 65493b72 6164 58 56 a2 616f 58 20 32ba11a1c05f8ad3cf9186989899450345c4c1171c3a2a6e8654ae8cedccfa91 6170 58 2d 3d24aae455f37dc9591e39d29bf7948b7c4c4a11ab47557a53ea58707ea6e180f346e25ff1855e92dcfdab150c
        header_byte = "10"
        length1 = "68" # I have seeing that this length may vary: 68, 69
        static_overall1 = "0000"
        static_overall2 = "a461610261620161631a"
        timestamp = str(hex(int(time.time())))[2:]
        static_overall3 = "6164"
        length2 = "5856" # I have seeing that this length may vary: 56, 57
        static_overall4 = "a2616f"
        length3 = "5820" # Static length
        unknown1 = os.urandom(32).hex() # 32ba11a1c05f8ad3cf9186989899450345c4c1171c3a2a6e8654ae8cedccfa91
        static_overall5 = "6170"
        length4 = "582d" # I have seeing that this length may vary: 2d, 2e
        unknown2 = os.urandom(45).hex() # 3d24aae455f37dc9591e39d29bf7948b7c4c4a11ab47557a53ea58707ea6e180f346e25ff1855e92dcfdab150c

        packet6Payload = header_byte + length1 + static_overall1 + static_overall2 + timestamp + static_overall3 + length2 + static_overall4 + length3 + unknown1 +static_overall5 + length4 + unknown2
        print("Step 4: Client sends a write request to 5e400002 with payload " + packet6Payload)
        await client.write_gatt_char(characteristic2, bytearray.fromhex(packet6Payload), response=True)
        print("Done with step 4. Next!")

        print("Waiting for NOTIFY after Step 4...")
        stop_event.clear()
        await stop_event.wait()
        
        # Step 5: Phone sends a WRITE request to 5e400002 with payload similar to: 103d0000a461610161620161631a66034fd46164582ba36161066162016166           58 20 1ec390ec3a998a4297b6541a7230ccefe138b6e2ccd00ad10fa3547f33ed714f
        # 10 3d 0000 a461610161620161631a 66034fd4 6164 58 2b a3 6161 06 6162 01 6166 58 20 1ec390ec3a998a4297b6541a7230ccefe138b6e2ccd00ad10fa3547f33ed714f
        header_byte = "10"
        length1 = "3d"
        static_overall1 = "0000"
        static_overall2 = "a461610161620161631a"
        timestamp = str(hex(int(time.time())))[2:]
        static_overall3 = "6164"
        length2 = "582b" # Static length
        static_overall4 = "a36161066162016166"
        length3 = "5820" # Static length
        unknown1 = os.urandom(32).hex() # 1ec390ec3a998a4297b6541a7230ccefe138b6e2ccd00ad10fa3547f33ed714f
        
        packet8Payload = header_byte + length1 + static_overall1 + static_overall2 + timestamp + static_overall3 + length2 + static_overall4 + length3 + unknown1
        print("Step 5: Client sends a write request to 5e400002 with payload " + packet8Payload)
        await client.write_gatt_char(characteristic2, bytearray.fromhex(packet8Payload), response=True)
        print("Done with step 5. Next!")

        print("Waiting for NOTIFY after Step 5...")
        stop_event.clear()
        await stop_event.wait()

        return 0

# Start script
asyncio.run(main())
print ("DONE!")
# ------------------------- END ---------------
