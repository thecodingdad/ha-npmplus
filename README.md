# NPMplus

Home Assistant integration for Nginx Proxy Manager Plus (NPMplus). Control proxy hosts and monitor their status.

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/v/release/thecodingdad/ha-npmplus)](https://github.com/thecodingdad/ha-npmplus/releases)

## Features

- Control proxy hosts directly from Home Assistant
- Enable or disable individual proxy hosts via switches
- Configurable polling interval for status updates
- Optional SSL certificate verification

## Prerequisites

- Home Assistant 2024.1.0 or newer
- Running NPMplus instance

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click "Explore & Download Repositories"
3. Search for "NPMplus"
4. Click "Download"
5. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub Releases](https://github.com/thecodingdad/ha-npmplus/releases)
2. Copy the `custom_components/npmplus` folder to your Home Assistant `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

### Setup

1. Go to **Settings** -> **Devices & Services**
2. Click **Add Integration**
3. Search for "NPMplus"
4. Follow the setup wizard

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `url` | string | required | NPMplus instance URL |
| `username` | string | required | Login username |
| `password` | string | required | Login password |
| `verify_ssl` | boolean | false | Enable SSL certificate verification |
| `scan_interval` | integer | 30 | Polling interval in seconds (5-3600) |

## Entities

The integration creates the following entities for each proxy host configured in your NPMplus instance.

### Switches

| Switch | Description |
|--------|-------------|
| Proxy Host | One switch per proxy host to enable or disable it |

## Multilanguage Support

This integration supports English and German.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
