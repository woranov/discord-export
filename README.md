# Discord Channel Exporter

Basic CLI tool using https://github.com/Tyrrrz/DiscordChatExporter to keep an up-to-date archive of selected Discord channels.

## Prerequisites

- Python 3.8 or later, no additional python dependencies required.
- [DiscordChatExporter.CLI](https://github.com/Tyrrrz/DiscordChatExporter/releases/latest) executable.

## Usage

Save your Discord API tokens in a `tokens.ini` file.

```ini
[main]
token = MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM
bot = True

[second-bot]
token = MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM
bot = True
```

Configure your export settings in `config.ini`.

```ini
; Base settings applied for all channels. See --help in DiscordChatExporter.CLI for details.
[DEFAULT]
partition = 1000
format = json
dateformat = u
token = main

; server-id
[81384788765712384]
name = discord-api

; server-id.channel-id
[81384788765712384.437410517242609684]
name = starboard
; This will automatically update after every export
after = 2024-01-01T00:00:00.000000
; settings can be overwritten at any level
partition = 100
token = second-bot
```

Run the script.

```
usage: python export.py [-h] [-o OUT] [-c CONFIG] [-t TOKENS] [-e EXECUTABLE]

optional arguments:
  -h, --help            show this help message and exit
  -o OUT, --out OUT     output directory
                        default: out
  -c CONFIG, --config CONFIG
                        path to config
                        default: config.ini
  -t TOKENS, --tokens TOKENS
                        path to tokens config
                        default: tokens.ini
  -e EXECUTABLE, --executable EXECUTABLE
                        path to exporter cli executable
                        see https://github.com/Tyrrrz/DiscordChatExporter/releases/
                        default: bin\DiscordChatExporter.CLI\DiscordChatExporter.Cli.exe
```