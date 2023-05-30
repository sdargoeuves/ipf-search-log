"""
General Python3 script for IP Fabric's API to get the list of available
log files and searches the specific input strings in it, prints the output.

2022-11 - version 1.0
Adaptation of the search_config script created by Milan. This time
we won't look in the config backup, but in the logs

WARNING: you should make sure the SDK version matches your version of IP Fabric
"""


import contextlib
import json
import os
import sys
from pathlib import Path

import dotenv
import typer
from ipfabric import IPFClient
from ipfabric.tools import DeviceConfigs
from modules.logs_dhcp import display_dhcp_interfaces, search_dhcp_interfaces
from modules.logs_ipf import display_log_compliance, download_logs, search_logs
from modules.logs_iosxr_rm import display_iosxr_rm, search_iosxr_rm

with contextlib.suppress(ImportError):
    from rich import print
# Get Current Path
CURRENT_FOLDER = Path(os.path.realpath(os.path.dirname(__file__)))
# CURRENT_PATH = Path(os.path.realpath(os.path.curdir)) # for testing only

app = typer.Typer(add_completion=False)


@app.command()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose mode."),
    dhcp_intf: bool = typer.Option(
        False,
        "--dhcp-interfaces",
        "-d",
        help="Check for interfaces configured as DHCP client",
    ),
    iosxr_rm: bool = typer.Option(
        False,
        "--iosxr_rm",
        "-xr",
        help="Check for IOSXR Route map information",
    ),
):
    """
    Script to look for a pattern, in a section, for a specific command output
    in the log file of IP Fabric
    """

    def valid_json(raw_data: str):
        """
        Confirm the env variable is a valid JSON. Return the json if OK, or exit.
        """
        if not raw_data:
            print("##ERR## The `INPUT_DATA` is not in the .env file.")
            sys.exit()
        try:
            json_data = json.loads(raw_data)
        except json.JSONDecodeError as exc:
            print(f"##ERR## The `INPUT_DATA` is not a valid JSON.\n{exc}\n'{raw_data}'")
            sys.exit()
        return json_data

    # Load environment variables
    dotenv.load_dotenv(dotenv.find_dotenv(), override=True)
    prompt_delimiter = os.getenv("PROMPT_DELIMITER")
    device_filter = valid_json(os.getenv("DEVICES_FILTER", "{}"))

    # Getting data from IP Fabric and printing output
    ipf_client = IPFClient(
        base_url=os.getenv("IPF_URL"),
        auth=os.getenv("IPF_TOKEN"),
        snapshot_id=os.getenv("IPF_SNAPSHOT", "$last"),
        verify=(os.getenv("IPF_VERIFY", "False") == "True"),
        timeout=10,
    )

    logs = DeviceConfigs(ipf_client)
    # Download log files for matching hostnames
    ipf_devices = ipf_client.inventory.devices.all(filters=device_filter)
    print(f"\nDOWNLOADING log files for {len(ipf_devices)} devices", end="")
    log_list = download_logs(logs, ipf_devices)

    # Search for specific strings in the log files
    print(f"\nSEARCHING through {len(log_list)} log files")
    if dhcp_intf:
        result = search_dhcp_interfaces(ipf_client, log_list, prompt_delimiter, verbose)
        display_dhcp_interfaces(result)
    elif iosxr_rm:
        result = search_iosxr_rm(ipf_client, log_list, verbose)
        display_iosxr_rm(result)
    else:
        input_data = valid_json(os.getenv("INPUT_DATA", ""))
        result = search_logs(input_data, log_list, prompt_delimiter, verbose)
        display_log_compliance(result)


if __name__ == "__main__":
    app()
