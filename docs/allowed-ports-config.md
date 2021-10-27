# Allowed ports config

## Intro
The allowed ports config is a json object used to specify exclutions before the the firewall is created.

Note: Incorrectly applying these rules will result in the firewall not blocking all outgoing traffic. Only disable the `internal` option if you know what you are doing!
## Setup
This config can be loaded through two options

- `--allow-config [string]` Specifies a path to a .json file containing the config.
- `--allow-config-json [string]` Allows for the json string to be passed directly as an argument.

## Schema
```json
[
    {
        "port": int || string,
        "protocol": (optional) string,
        "internal": (optional) bool
        "allowed_ip_range": (optional) str[] || str
    },
    ...
]
```

## Details

### Port
This option specifies what port(s) should be excluded by this rule. This option is required.

Can either be passed as an integer between `1` and `65535`; a string or a port range in the form of `{port_lower}-{port_upper}`

### Protocol
This option defines the protocols the ports will be opened on. This defaults to `tcp`.

This can be either be set to `tcp`, `udp` or `both`.

### Internal
This option specifies if ports should be only allowed on internal IP ranges. When set to `true` this will only allow ports to be exposed in the local network

Note: this option is overridden if extra IPs are set in

### Allowed IP Range
This option specifies the ip(s) that the specified port(s) should be exposed to. This can either be a specific IP or an IP block.

This can either be passed as a single IP (as a string) or an array of ips (as an array of srings). This can also be used 

This defaults to null.

## Examples
```json
[
    {
        "port": 22,
        "protocol": "both"
    }
]
```
Expose on the external network port `22` on both `tcp` and `udp` protocols.

```json
[
    {
        "port": "137-139",
        "protocol": "udp",
        "internal": false
    }
]
```
Expose ports 137, 138 and 139 over UDP to the clear net while the firewall is up
