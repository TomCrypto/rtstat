rtstat v0.1
===========

This is a Python 3 tool to extract useful information from routers via telnet (using `telnetlib`) in JSON format. The data obtained can then be saved and used later e.g. to graph data usage peaks, visualize modem disconnections, measure router uptime and monitor a variety of interfaces. Currently only one router is supported, the Thomson TG585 v8 model which I am using, and only a very small subset of all available information is currently retrieved. Example usage and output:

    $ rtstat --router TG585v8 --host 192.168.1.254
    {
        "data": {
            "iflist": {
                "lan": {
                    "rx": 18908913,
                    "tx": 394918736
                },
                "local": {
                    "rx": 15927004,
                    "tx": 1602303
                },
                "wan": {
                    "rx": 380311813,
                    "tx": 18085434
                }
            },
            "xdsl-info": {
                "bandwidth-down": 1973250,
                "bandwidth-up": 151000,
                "state": "up",
                "type": "ADSL2+",
                "uptime": 7565
            }
        },
        "router": "Thomson TG585 v8",
        "timestamp": 1426927484.2418256
    }

The script is extensible and other router models can be easily added by adding a new router class and implementing its `get_all_info` and `name` methods. I did not however attempt to enforce the specific information retrieved, so each router class is free to parse and return any information it pleases as a JSON-compatible dictionary as long as it is useful and easily parsable; for instance, in the JSON chunk above the uptime is in seconds and the rx/tx/bandwidth values are in bytes and bytes per second respectively. One way of consuming the information retrieved could be to store each snapshot on disk and then plot quantities of interest as a function of the provided Unix timestamp using any graphing tool.

This tool is mostly for my personal usage but maybe someone else will find it or the code useful. If you extend it to support another router model I would welcome a pull request. I am not really interested in Python 2 compatibility but since the code involves mostly data parsing it will probably be easy to make it run under Python 2.7 at least (as it turns out, this version does run on Python 2.7 without issues).

Installation and Usage
----------------------

    $ python3 setup.py install
    $ rtstat --help

License
-------

Released under the MIT license. See the LICENSE file for more information.
