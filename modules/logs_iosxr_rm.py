"""
Set of functions to download log file from IP Fabric and search through those
2022-11 - version 1.0
"""

import contextlib
import re

from ipfabric import IPFClient

with contextlib.suppress(ImportError):
    from rich import print


def display_log_iosxr_rm(result: list):
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


def search_iosxr_rm(ipf_client: IPFClient, log_list, verbose: bool = False):
    """A function to search for all BGP neighbor, if a route maps exists
    Attributes:
    ----------
    input_strings: list of strings
        the list of strings to search for
    log_list: list of objects
        object items containing hostnames, log files, ..
    """

    def get_device_bgp_neighbors(ipf_client: IPFClient, sn: str):
        """
        Return the list of BGP neighbors for a device
        """
        filter_bgp_neighbors = {"sn": ["eq", sn]}
        return ipf_client.technology.routing.bgp_neighbors.all(
            filters=filter_bgp_neighbors
        )

    def search_through_log(input_string: dict, method: str):
        result = []
        for log in log_list:
            # we search and extract the output for the section
            print("|", end="")
            if input_string["section"] == "":
                section_extract = [log["text"]]
            else:
                section_pattern = rf'({input_string["section"]}(.*?){input_string["section_delimiter"]})'
                section_regex = re.compile(section_pattern, re.MULTILINE | re.DOTALL)
                section_extract = section_regex.search(log["text"])
            if section_extract:
                # we search and extract the section for each BGP neighbor
                for bgp_neighbor in get_device_bgp_neighbors(ipf_client, log["sn"]):
                    # create a deepcopy to edit the item without affecting input_strings
                    # item = copy.deepcopy(input_string)
                    print(".", end="")
                    item = {}
                    item["hostname"] = log["hostname"]
                    item["neiAddress"] = (
                        bgp_neighbor["neiAddress"]
                        if bgp_neighbor["neiAddress"] != None
                        else bgp_neighbor["neiAddressV6"]
                    )
                    pattern = rf'{input_string["match"]}{item["neiAddress"]}(.*?){input_string["match_delimiter"]}'
                    section_regex = re.compile(pattern, re.MULTILINE | re.DOTALL)
                    if sub_section := section_regex.search(section_extract[0]):
                        present_in_log = "yes"
                        # in here the sub section contains the information for that BGP neighbor, we collect description and route-policy
                        # Extract description
                        description_pattern = rf"{input_string['description']}"
                        description_regex = re.compile(
                            description_pattern, re.MULTILINE | re.DOTALL
                        )
                        description_match = description_regex.search(sub_section[0])
                        if description_match and description_match[1]:
                            item[f"description_{method}"] = description_match[1]
                        else:
                            item[f"description_{method}"] = "not_specified"
                        # Extract route-policies
                        route_policy_pattern = rf"{input_string['policy_route']}"
                        route_policy_matches = re.findall(
                            route_policy_pattern, sub_section[0]
                        )
                        if route_policy_matches:
                            route_policies = []
                            for match in route_policy_matches:
                                if match[0] in ["incoming", "outgoing"]:
                                    route_policies.append(
                                        {
                                            "name": match[1],
                                            "direction": "in"
                                            if match[0] == "incoming"
                                            else "out",
                                        }
                                    )
                                else:
                                    route_policies.append(
                                        {"name": match[0], "direction": match[1]}
                                    )
                            item[f"route-policy_{method}"] = route_policies
                        else:
                            item[f"route-policy_{method}"] = "not_specified"

                    else:
                        present_in_log = f"^ neighbor {item['neiAddress']} not found"
                    if verbose:
                        item["found"] = present_in_log
                    result.append(item)

            else:
                item = {}
                present_in_log = "`^router bgp` not found in log file"
                item["hostname"] = log["hostname"]
                item["found"] = present_in_log
                result.append(item)
        return result

    search_sh_run = {
        "section": "^router bgp (\d)",
        "section_delimiter": "^!\r\n",
        "match": "^\s+neighbor ",
        "match_delimiter": "^\s+!\r\n",
        "description": "description ([^\r\n]+)",
        "policy_route": "route-policy\s+(.*?)\s+(in|out)",
    }
    list_sh_run = search_through_log(search_sh_run, "shrun")
    return list_sh_run

    ## this is the part where we check the same information via the show bgp
    ## instead of the sh run
    # search_sh_bgp = {
    #     "section": "#\x07sho bgp",
    #     "section_delimiter": "#\x07show mpls",
    #     # "section": "#\x07sho bgp vrf all neighbors\r\n",
    #     # "section_delimiter": "#\x07sho",
    #     "match": "^BGP neighbor is ",
    #     "match_delimiter": "(\r\n\r\nBGP neighbor is|#\x07sho)",
    #     "description": "Description: ([^\r\n]+)",
    #     "policy_route": "Policy for (incoming|outgoing) advertisements is (\S+\s?\S+)",
    # }
    # print("")
    # list_sh_bgp = search_through_log(search_sh_bgp, "shbgp")
    #
    ##Now we merge both table and dsiplay shrun & shbgp info if different
    # merged_list = []
    # for dict_sh_run in list_sh_run:
    #     for dict_sh_bgp in list_sh_bgp:
    #         new_dict = dict_sh_run.copy()
    #         if dict_sh_run.get("hostname") == dict_sh_bgp.get(
    #             "hostname"
    #         ) and dict_sh_run.get("neiAddress") == dict_sh_bgp.get("neiAddress"):
    #             # we found the same neighbor, let's check description
    #             if dict_sh_run["description_shrun"] == dict_sh_bgp["description_shbgp"]:
    #                 new_dict["description"] = new_dict.pop("description_shrun")
    #             else:
    #                 new_dict["description_shbgp"] = dict_sh_bgp["description_shbgp"]
    #             #and now check the rote-policy
    #             if (
    #                 dict_sh_run["route-policy_shrun"]
    #                 == dict_sh_bgp["route-policy_shbgp"]
    #             ):
    #                 new_dict["route-policy"] = new_dict.pop("route-policy_shrun")
    #             else:
    #                 new_dict["route-policy_shbgp"] = dict_sh_bgp["route-policy_shbgp"]
    #         merged_list.append(new_dict)

    # return merged_list
