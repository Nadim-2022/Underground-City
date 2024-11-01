import re
import sys
import asyncio
import argparse


from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice as BleakDevice
from typing import Dict, Any, List

# Map of devices indexed by name
devices: Dict[str, BleakDevice] = {}

# Scan callback to also catch nonconnectable scan responses
def _scan_callback(device: BleakDevice, _: Any) -> None:
    # Add to the dict if not unknown
    if device.name and device.name != "Unknown":
        devices[device.name] = device

# Asynchronous function to discover BLE devices
async def discover_devices(identifier: str):
    # Use BleakScanner to discover devices and pass the callback
    await BleakScanner.discover(timeout=5, detection_callback=_scan_callback)

    # Create a regex token to match the identifier
    token = re.compile(identifier or r"GoPro [A-Z0-9]{4}")

    # Now look for our matching device(s)
    matched_devices: List[BleakDevice] = [device for name, device in devices.items() if token.match(name)]

    if matched_devices:
        print(f"Found {len(matched_devices)} matching device(s):")
        for device in matched_devices:
            print(f"- {device.name} ({device.address})")
    else:
        print("No matching devices found.")

    # We're just taking the first device if there are multiple.
    device = matched_devices[0]
    client = BleakClient(device)
    await client.connect(timeout=15)
    try:
        await client.pair()
        if await client.is_connected():
            print("Paired with device")
    except NotImplementedError:
        # This is expected on Mac
        print("Pairing is not implemented on this platform.")
        pass
    
    # Sleep for a bit to allow the pairing to complete
    await asyncio.sleep(60)

# Argument parser for command-line input
def parse_args():
    parser = argparse.ArgumentParser(description="Discover BLE devices and filter by identifier.")
    parser.add_argument("-i", "--identifier", help="Regular expression to match device name (e.g., GoPro [A-Z0-9]{4}).", default=r"GoPro [A-Z0-9]{4}")
    return parser.parse_args()

# Main function to run the async discovery
if __name__ == "__main__":
    args = parse_args()

    # Run the asynchronous discovery function with the identifier
    asyncio.run(discover_devices(args.identifier))
