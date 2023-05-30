# ipf-search-logs

Project based on the `ipf-search-config` project, this time focusing on searching inside the IPF logs instead of the configuration backup. This allows for more specific searches.

## How to install

Install ipfabric Python module and dependencies. Make sure the version of the `ipfabric` SDK matches your version of IP Fabric.

```shell
pip install -r requirements.txt
```

## How to use

### Environment file

You need to copy the `.env.example` file:

```zsh
cp .env.example .env
```

In the file `.env` you have created, you will need to set the variables:

* `IPF_URL = "https://ipfabric-server/"` enter the URL of IP Fabric
* `IPF_TOKEN = "abcd1234"` enter the API token
* `IPF_VERIFY = "True"` use False if you are using a self-signed certificate
* `IPF_SNAPSHOT` leave blank if you want to use the latest snapshot, otherwise add the `id` of the snapshot, i.e. `66365ad3-e568-403a-91a3-de1775b4f600`
* `PROMPT_DELIMITER = "#"` this is the sign directly after the hostname from the command line, this is for us to know where to start the search for a command. For example, on Cisco, if you are in enabled mode you would use `#`
* `DEVICES_FILTER = '{"hostname": ["like", "L35AC12"]}'` This is the filter used to get the list of devices for which we want to search the specific string, in the command_section. To create the filter, you can use the `?` on the inventory table of IP Fabric to see how the filter is generated.

* `INPUT_DATA` is the list of string/value we want to search for in the log.
  * `ref` is an optional field
  * `command` specifies in which command section we should look for this command, from the IP Fabric log
  * `section` (*optional*) inside the command section, we will only look for a specific sub-section
  * `match` is the string we are looking for in the command section, inside the section if specified, of the log file.

Example:

```text
INPUT_DATA = '[
    {"ref": "1.1.1", "command": "show ip interface", "section": "Loopback", "match": "MTU is 1514"},
    {"ref": "1.1.2", "command": "sh run", "section": "ntp" , "match": "10.0.10.10"}
]'
```

### Run the script

Running the python script this way will give you an update showing what is compliant: `match` string has been found, and what is not compliant.

```zsh
python3 search_logs.py
```

You can also use the *verbose* mode which will show you what has been matched.

```zsh
python3 search_logs.py -v
```

There is also a `-d` option to check for interfaces with IP address assigned by DHCP

```zsh
python3 search_logs.py -d
```

## Help

```zsh
python3 search_logs.py --help
```

## License

MIT

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

[//]: # (These are reference links used in the body of this note and get stripped out when the markdown processor does its job.)
