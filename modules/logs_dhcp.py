"""
Set of functions to download log file from IP Fabric and search through those
2022-11 - version 1.0
"""

import contextlib
import copy
import re

from ipfabric import IPFClient

with contextlib.suppress(ImportError):
    from rich import print


def display_dhcp_interfaces(result: list):
    """
    Takes the result and display if an interfce is conigured via DHCP or not
    """
    result_ok = []
    result_nok = []
    for check in result:
        if check["found"] == "DHCP":
            result_ok.append(check)
        else:
            result_nok.append(check)
    print("\n------------- INTERFACES with DHCP -------------")
    print(result_ok)
    print("\n!!!!!!!!!!!!! INTERFACES NOT with DHCP !!!!!!!!!!!!!")
    print(result_nok)


def search_dhcp_interfaces(
    ipf_client: IPFClient, log_list, prompt_delimiter: str, verbose: bool = False
):
    """A function to search if an Interface with an IP has been allocated via DHCP or not
    Attributes:
    ----------
    input_strings: list of strings
        the list of strings to search for
    log_list: list of objects
        object items containing hostnames, log files, ..
    """

    def get_device_interfaces(ipf_client: IPFClient, sn: str):
        """
        Return the list of relevant interfaces -> assigned with an IP Address
        """
        filter_interfaces_with_ip = {
            "and": [{"primaryIp": ["empty", False]}, {"sn": ["eq", sn]}]
        }
        return ipf_client.inventory.interfaces.all(filters=filter_interfaces_with_ip)

    result = []
    input_string = {
        "command": "show ip interface",
        "match": "Address determined by DHCP",
    }
    for log in log_list:
        # we search and extract the output for the show ip interface command
        command_pattern = rf'(^{log["hostname"]}{prompt_delimiter}.{input_string["command"]}.*[\s\S]*?(?={log["hostname"]}{prompt_delimiter}))'
        command_regex = re.compile(command_pattern, re.MULTILINE)
        if command_section := command_regex.search(log["text"]):
            # we search and extract the section for each interface
            for interface in get_device_interfaces(ipf_client, log["sn"]):
                # create a deepcopy to edit the item without affecting input_strings
                # item = copy.deepcopy(input_string)
                item = {}
                item["hostname"] = log["hostname"]
                item["interface"] = interface["nameOriginal"]
                pattern = rf'(^{item["interface"]}.*$[\n\r]*(?:^\s.*$[\n\r]*)*)'
                section_regex = re.compile(pattern, re.MULTILINE)
                if section := section_regex.search(command_section[0]):
                    present_in_log = (
                        "DHCP" if input_string["match"] in section[0] else "NOT DHCP"
                    )
                    if verbose:
                        item["matched_section"] = section[0]
                else:
                    present_in_log = f"Interface `{item['interface']}` not found"
                item["found"] = present_in_log
                result.append(item)

        else:
            present_in_log = "`show ip interface` not found`"
            item["hostname"] = log["hostname"]
            item["found"] = present_in_log
            result.append(item)
    return result
