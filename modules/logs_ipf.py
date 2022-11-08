"""
Set of functions to download log file from IP Fabric and search through those
2022-11 - version 1.0
"""
import copy
import re

try:
    from rich import print
except ImportError:
    None


def download_logs(logs, ipf_devices: list):
    """
    Function to download the IP Fabric log of provided list of devices
    """
    return_list = []
    for host in ipf_devices:
        print(".", end="")
        #ipdb.set_trace()
        # Get the log file
        if dev_log := logs.get_text_log(host):
            return_list.append(
                {
                    **{
                        "hostname": host["hostname"],
                        "text": dev_log,
                    },
                }
            )
    return return_list


def search_logs(input_strings, log_list, verbose: bool = False):
    # sourcery skip: low-code-quality
    """A function to search for a specific list of string within the list of log files.
    Attributes:
    ----------
    input_strings: list of strings
        the list of strings to search for
    log_list: list of objects
        object items containing hostnames, log files, ..
    """
    result = []
    for log in log_list:
        for input_string in input_strings:
            # create a deepcopy to edit the item without affecting input_strings
            item = copy.deepcopy(input_string)
            if "command" in item.keys():
                # we extract the output for the specified command
                command_pattern = rf'(^{log["hostname"]}{item["delimiter"]}.{item["command"]}.*[\s\S]*?(?={log["hostname"]}{item["delimiter"]}))'
                command_regex = re.compile(command_pattern, re.MULTILINE)
                if command_section := command_regex.search(log["text"]):
                    if "section" in item.keys():
                        # we extract the section within the output of the command
                        pattern = rf'(^{item["section"]}.*$[\n\r]*(?:^\s.*$[\n\r]*)*)'
                        section_regex = re.compile(pattern, re.MULTILINE)
                        if section := section_regex.search(command_section[0]):
                            present_in_log = "YES" if item["match"] in section[0] else "NO"
                            if verbose:
                                item["matched_section"] = section[0]
                        else:
                            present_in_log = "SECTION NOT FOUND"
                    else:
                        present_in_log = "YES - NO SECTION" if item["match"] in command_section[0] else "NO - NO SECTION"
                        if verbose:
                            item["matched_section"] = command_section[0]
                else:
                    present_in_log = "COMMAND NOT FOUND"
            else:
                present_in_log = "COMMAND NOT SPECIFIED"
            item["hostname"] = log["hostname"]
            item["found"] = present_in_log
            del item["delimiter"]
            result.append(item)
    return result