import argparse
import asyncio
from typing import Any

from rich.console import Console

from open_gopro import Params, WirelessGoPro, constants, proto
from open_gopro.logger import setup_logging
from open_gopro.util import add_cli_args_and_parse, ainput

console = Console()  # rich consoler printer

async def setup_livestream(gopro: WirelessGoPro, args: argparse.Namespace, ssid: str, password: str, url: str) -> None:
    await gopro.ble_command.set_shutter(shutter=Params.Toggle.DISABLE)
    await gopro.ble_command.register_livestream_status(
        register=[proto.EnumRegisterLiveStreamStatus.REGISTER_LIVE_STREAM_STATUS_STATUS]
    )

    console.print(f"[yellow]Connecting to {ssid}...")
    await gopro.connect_to_access_point(ssid, password)

    # Start livestream
    livestream_is_ready = asyncio.Event()

    async def wait_for_livestream_start(_: Any, update: proto.NotifyLiveStreamStatus) -> None:
        if update.live_stream_status == proto.EnumLiveStreamStatus.LIVE_STREAM_STATE_READY:
            livestream_is_ready.set()

    console.print("[yellow]Configuring livestream...")
    gopro.register_update(wait_for_livestream_start, constants.ActionId.LIVESTREAM_STATUS_NOTIF)
    await gopro.ble_command.set_livestream_mode(
        url=url,
        window_size=args.resolution,
        minimum_bitrate=args.min_bit,
        maximum_bitrate=args.max_bit,
        starting_bitrate=args.start_bit,
        lens=args.fov,
    )

    # Wait to receive livestream started status
    console.print("[yellow]Waiting for livestream to be ready...\n")
    await livestream_is_ready.wait()

    # TODO Is this still needed?
    await asyncio.sleep(2)

    console.print("[yellow]Starting livestream")
    assert (await gopro.ble_command.set_shutter(shutter=Params.Toggle.ENABLE)).ok

    console.print("[yellow]Livestream is now streaming and should be available for viewing.")
    await ainput("Press enter to stop livestreaming...\n")

    await gopro.ble_command.set_shutter(shutter=Params.Toggle.DISABLE)
    await gopro.ble_command.release_network()

async def main(args: argparse.Namespace) -> None:
    setup_logging(__name__, args.log)

    async with WirelessGoPro(args.identifier1, enable_wifi=False) as gopro1, \
               WirelessGoPro(args.identifier2, enable_wifi=False) as gopro2:
        await asyncio.gather(
            setup_livestream(gopro1, args, args.ssid1, args.password1, args.url1),
            
            setup_livestream(gopro2, args, args.ssid2, args.password2, args.url2)
        )

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Connect to two GoPros via BLE only, configure then start Livestreams, then display them with CV2."
    )
    # Set default values for ssid, password, and url
    parser.add_argument("identifier1", type=str, help="Identifier for the first GoPro.")
    parser.add_argument("ssid1", type=str, help="WiFi SSID to connect to for the first GoPro.", nargs='?', default="TP-Link_A2FC")
    parser.add_argument("password1", type=str, help="Password of WiFi SSID for the first GoPro.", nargs='?', default="nadimahmed")
    parser.add_argument("url1", type=str, help="RTMP server URL to stream to for the first GoPro.", nargs='?', default="rtmp://192.168.0.246:1935/live/mystream")
    parser.add_argument("identifier2", type=str, help="Identifier for the second GoPro.")
    parser.add_argument("ssid2", type=str, help="WiFi SSID to connect to for the second GoPro.", nargs='?', default="TP-Link_A2FC")
    parser.add_argument("password2", type=str, help="Password of WiFi SSID for the second GoPro.", nargs='?', default="nadimahmed")
    parser.add_argument("url2", type=str, help="RTMP server URL to stream to for the second GoPro.", nargs='?', default="rtmp://192.168.0.246:1935/live/mystream2")
    parser.add_argument("--min_bit", type=int, help="Minimum bitrate.", default=100)
    parser.add_argument("--max_bit", type=int, help="Maximum bitrate.", default=100)
    parser.add_argument("--start_bit", type=int, help="Starting bitrate.", default=100)
    parser.add_argument(
        "--resolution", help="Resolution.", choices=list(proto.EnumWindowSize.values()), default=None, type=int  # type: ignore
    )
    parser.add_argument(
        "--fov", help="Field of View.", choices=list(proto.EnumLens.values()), default=None, type=int  # type: ignore
    )
    return add_cli_args_and_parse(parser, wifi=False)

def entrypoint() -> None:
    asyncio.run(main(parse_arguments()))

if __name__ == "__main__":
    entrypoint()