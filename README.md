# PyGPSClient

PyGPSClient is a graphical GNSS/GPS testing and diagnostic client application written entirely in Python and tkinter.

![full app screenshot](/images/all_widgets2.png)

The application runs on any platform which supports a Python3 interpreter (>=3.6) and tkinter (>=8.6) GUI framework, 
including Windows, MacOS, Linux and Raspberry Pi OS. It displays location and diagnostic data from any NMEA or UBX (u-blox &copy;) 
compatible GNSS/GPS device over a standard serial (UART) or USB port, *in addition to* providing a small but useful subset of the 
configuration functionality in u-blox's Windows-only [u-center](https://www.u-blox.com/en/product/u-center) tool.

This is a personal project and I have no affiliation whatsoever with u-blox &copy;.

## Features:

1. Supports both NMEA and UBX protocols. It uses the existing pynmea2 library for NMEA parsing and 
implements a **[new pyubx2 library](https://github.com/semuconsulting/pyubx2)** for UBX parsing. 
1. Configurable GUI with selectable and resizeable widgets.
1. Expandable banner widget showing key navigation information.
1. Serial console widget showing either raw or parsed data stream.
1. Skyview widget showing current satellite visibility and position (elevation / azimuth).
1. Graphview widget showing current satellite reception (signal-to-noise ratio).
1. Mapview widget with location marker, showing either a static Mercator world map, or an optional dynamic web-based map downloaded via a MapQuest API (requires an Internet connection and free 
[MapQuest API Key](https://developer.mapquest.com/plan_purchase/steps/business_edition/business_edition_free/register)).
1. UBX Configuration Dialog, with the ability to send a variety of UBX configuration messages to u-blox GNSS devices. This includes the facility to add **user-defined preset configuration messages** - see instructions under [installation](#installation) below.

![sats & mercator widget screenshot](/images/sats_mercator_widget.png)

### UBX Configuration Facilities
![ubxconfig widget screenshot](/images/ubxconfig_widget.png)

The UBX Configuration Dialog currently supports the following UBX configuration commands:
1. CFG-PRT sets baudrate and inbound/outbound protocols across all available ports 
(*note that* an active USB port will always report a baudrate of 0).
1. CFG-MSG sets message rates per port for NMEA protocol messages (standard & proprietary) and UBX protocol messages.
1. PRESET commands support a variety of preset and user-defined commands - see [user defined presets](#userdefined)

An icon to the right of each 'SEND' button indicates the latest polled state of the displayed configuration 
(pending, confirmed or warning). **NB** this is not a 100% reliable indication as the UBX protocol does not
support explicit command handshaking, and confirmation responses can occasionally get lost or delayed in heavy
inbound traffic. To ensure timely confirmation responses, try temporarily disabling periodic inbound traffic 
using the preset commands provided.

#### Glossary of Terms

* utc - coordinated universal time 
* siv - satellites in view
* sip - satellites used in position solution
* dop - [dilution of precision](https://gisgeography.com/gps-accuracy-hdop-pdop-gdop-multipath/) (pdop - position, hdop - horizontal, vdop - vertical)
* acc - accuracy of location in real units (hacc - horizontal, vacc - vertical)

### Current Status

![Release](https://img.shields.io/github/v/release/semuconsulting/PyGPSClient?include_prereleases)
![Release Date](https://img.shields.io/github/release-date-pre/semuconsulting/PyGPSClient)
![Last Commit](https://img.shields.io/github/last-commit/semuconsulting/PyGPSClient)
![Contributors](https://img.shields.io/github/contributors/semuconsulting/PyGPSClient.svg)
![Open Issues](https://img.shields.io/github/issues-raw/semuconsulting/PyGPSClient)

Alpha. Main application and widgets are fully functional for both NMEA and UBX protocols.

Known Issues:
1. Application menu options can occasionally become momentarily unresponsive in heavy inbound traffic 
due to serial read blocking. This is in hand.

Constructive feedback welcome.

## <a name="installation">Installation</a>

![Python version](https://img.shields.io/pypi/pyversions/PyGPSClient.svg?style=flat)

In the following, `python` refers to the python3 executable. You may need to type `python3`, depending on your particular environment.

### Dependencies

See [requirements.txt](requirements.txt).

On Windows and MacOS, pip, tkinter and the necessary imaging libraries are generally packaged with Python.  On some Linux distributions like Ubuntu 18+ and Raspberry Pi OS, they may need to be installed separately, e.g.:

`sudo apt-get install python3-pip python3-tk python3-pil python3-pil.imagetk`

The following python libraries are required (these will be installed automatically if using pip to install PyGPSClient):

`python -m pip install pyubx2 pyserial pynmea2 Pillow requests`

### User Privileges

To access the serial port on most linux platforms, you will need to be a member of the 
`tty` and `dialout` groups. Other than this, no special privileges are required.

### 1. Install using pip

[![PyPI version](https://img.shields.io/pypi/v/PyGPSClient.svg?style=flat)](https://pypi.org/project/PyGPSClient/)
![PyPI downloads](https://img.shields.io/pypi/dm/PyGPSClient.svg?style=flat)

The easiest way to install PyGPSClient is via [pip](http://pypi.python.org/pypi/pip/):

`python -m pip install PyGPSClient`

To run the appliation, if the python3 site_packages are in your PATH, simply type `python -m pygpsclient`.

If not, type `python -m \full_path_to_site_packages\pygpsclient`.

### 2. Manual installation

To install manually, download and unzip this repository and run:

`python -m /path_to_folder/foldername/pygpsclient`

e.g. if you downloaded and unzipped to a folder named `PyGPSClient-0.2.0`, run: 

`python -m /path_to_folder/PyGPSClient-0.2.0/pygpsclient`.

### MapQuest API Key

To use the optional dynamic web-based mapview facility, you need to request and install a 
[MapQuest API key](https://developer.mapquest.com/plan_purchase/steps/business_edition/business_edition_free/register).
The free edition of this API allows for up to 15,000 transactions/month (roughly 500/day) on a non-commercial basis.
For this reason, the map refresh rate is intentionally limited to 1/minute to avoid exceeding the free transaction
limit under normal use. **NB:** this facility is *not* intended to be used for real time navigational purposes.

Once you have received the API key (a 32-character alphanumeric string), copy it to a file named `mqapikey` (lower case, 
no extension) and place this file in the user's home directory.

### <a name="userdefined">User Defined Presets</a>

The UBX Configuration Dialog includes the facility to add user-defined preset UBX configuration messages. These can be set up by adding
appropriate comma-delimited message descriptions and payload definitions to a file named `ubxpresets` (lower case, no extension), and then placing this file in the user's home directory. The message definition comprises a free-format text description (*avoid embedded commas*) 
followed by one or more [pyubx2 UBXMessage constructors](https://pypi.org/project/pyubx2/), i.e. 
1. ubx_class as a string e.g. `CFG` (must be a valid class from pyubx2.UBX_CONFIG_CATEGORIES)
2. ubx_id as a string e.g. `CFG-MSG` (must be a valid id from pyubx2.UBX_CONFIG_MESSAGES)
3. payload as a hexadecimal string e.g. `f004010100010100`
4. mode as an integer (`1` = SET, `2` = POLL)

Multiple commands can be concatenated on a single line. An illustrative example is given below:

```
CFG-MSG Enable RMC message, CFG, CFG-MSG, f004010100010100, 1
CFG-MSG Enable VTG message, CFG, CFG-MSG, f005010100010100, 1
CFG-MSG Enable UBX00 & UBX03 messages, CFG, CFG-MSG, f100010100010100, 1, CFG, CFG-MSG, f103010100010100, 1
```

## License

![License](https://img.shields.io/github/license/semuconsulting/PyGPSClient.svg)

BSD 3-Clause License

Copyright (c) 2020, SEMU Consulting
All rights reserved.

Application icons from [iconmonstr](https://iconmonstr.com/) &copy;.

## Author Information

semuadmin@semuconsulting.com
