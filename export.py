import argparse
import configparser
import datetime
import pathlib
import subprocess
import sys
from os import PathLike
from typing import Any, List, NamedTuple, Optional, Union

DEFAULT_GLOBAL_CONFIG = pathlib.Path("./config.ini")
DEFAULT_TOKENS_CONFIG = pathlib.Path("./tokens.ini")
DEFAULT_OUT_DIR = pathlib.Path("./out")
DEFAULT_BIN_DIR = pathlib.Path("./bin")
DEFAULT_EXECUTABLE = (
    DEFAULT_BIN_DIR / "DiscordChatExporter.CLI" / "DiscordChatExporter.Cli.exe"
)


ArgsList = List[Union[PathLike, str]]


class Guild(NamedTuple):
    id: int
    name: str


class Channel(NamedTuple):
    id: int
    name: str


class Token(NamedTuple):
    token: str
    bot: bool

    def args(self) -> List[str]:
        return ["-t", self.token] + (["-b"] if self.bot else [])

    @classmethod
    def from_config(
        cls, tokens_config: configparser.ConfigParser, token_name: str = "main"
    ) -> "Token":
        token = tokens_config.get(token_name, "token")
        is_bot = tokens_config.getboolean(token_name, "bot", fallback=True)

        return Token(token, bot=is_bot)


class Export(NamedTuple):
    guild: Guild
    channel: Channel
    token_name: str = "main"
    output_format: str = "json"
    datetime_format: str = "u"
    after: Optional[datetime.datetime] = None
    partition: Optional[int] = None

    @property
    def filename(self) -> str:
        ts = self.after or datetime.datetime.utcnow()
        return (
            f"{self.guild.name}-"
            f"{self.channel.name}-"
            f"{self.channel.id}-"
            f"{int(ts.timestamp())}"
            f".{self.output_format}"
        )

    def args(self, out_dir: PathLike) -> ArgsList:
        out: ArgsList = [
            "-c",
            str(self.channel.id),
            "-o",
            f"{out_dir}/{self.filename}",
            "-f",
            self.output_format,
            "--dateformat",
            self.datetime_format,
        ]
        if self.after:
            out.extend(["--after", self.after.isoformat()])
        if self.partition:
            out.extend(["-p", str(self.partition)])

        return out

    @classmethod
    def from_config(
        cls, config: configparser.ConfigParser, channel_section: str
    ) -> "Export":
        guild_id, _, channel_id = channel_section.partition(".")
        guild_name = config.get(guild_id, "name")
        channel_name = config.get(channel_section, "name")

        guild_section = guild_id

        guild = Guild(int(guild_id), guild_name)
        channel = Channel(int(channel_id), channel_name)

        key_aliases = {"token": "token_name"}

        def alias(key: str) -> str:
            return key_aliases.get(key, key)

        def value(key: str, section: str = channel_section) -> Optional[Any]:
            if key == "partition":
                return config.getint(section, key)
            elif key == "after":
                return datetime.datetime.fromisoformat(config.get(section, key))
            elif alias(key) in cls._fields:
                return config.get(section, key)
            else:
                return None

        def section_data(section):
            return {
                alias(k): v
                for k in config.options(section)
                if (v := value(k, section)) is not None
            }

        return cls(
            guild=guild,
            channel=channel,
            **{**section_data(guild_section), **section_data(channel_section)},
        )


def run_export(
    export: Export,
    config: configparser.ConfigParser,
    tokens: configparser.ConfigParser,
    executable: PathLike,
    out_dir: PathLike,
    config_filename: Optional[PathLike] = None,
) -> int:
    token = Token.from_config(tokens, token_name=export.token_name)

    args: ArgsList = [
        executable,
        "export",
        *export.args(out_dir=out_dir),
        *token.args(),
    ]

    try:
        subprocess.check_output(args, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as exc:
        if "contains no messages for the specified period" in exc.stderr.decode(
            sys.getfilesystemencoding()
        ):
            print("skipping, no new messages")
        else:
            raise

    config.set(
        f"{export.guild.id}.{export.channel.id}",
        "after",
        datetime.datetime.utcnow().isoformat(),
    )

    if config_filename:
        with open(config_filename, "w") as f:
            config.write(f)

    return 0


def load_config(
    filename: PathLike = DEFAULT_GLOBAL_CONFIG,
) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(filename)
    return config


def load_tokens_config(
    filename: PathLike = DEFAULT_TOKENS_CONFIG,
) -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    config.read(filename)
    return config


def run_all(
    config: configparser.ConfigParser,
    tokens: configparser.ConfigParser,
    executable: PathLike = DEFAULT_EXECUTABLE,
    out_dir: PathLike = DEFAULT_OUT_DIR,
    config_filename: Optional[PathLike] = None,
) -> int:
    channel_sections = []

    for section in config:
        if "." in section:
            channel_sections.append(section)

    for channel_section in channel_sections:
        print(
            f"exporting channel {channel_section} - {config.get(channel_section, 'name')}"
        )

        channel_export = Export.from_config(config, channel_section=channel_section)

        run_export(
            channel_export,
            config=config,
            tokens=tokens,
            executable=executable,
            out_dir=out_dir,
            config_filename=config_filename,
        )

    return 0


def main() -> int:
    # noinspection PyTypeChecker
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        "-o",
        "--out",
        default=DEFAULT_OUT_DIR,
        help="output directory\ndefault: %(default)s",
    )
    parser.add_argument(
        "-c",
        "--config",
        default=DEFAULT_GLOBAL_CONFIG,
        help="path to config\ndefault: %(default)s",
    )
    parser.add_argument(
        "-t",
        "--tokens",
        default=DEFAULT_TOKENS_CONFIG,
        help="path to tokens config\ndefault: %(default)s",
    )
    parser.add_argument(
        "-e",
        "--executable",
        default=DEFAULT_EXECUTABLE,
        help=(
            "path to exporter cli executable\n"
            "see https://github.com/Tyrrrz/DiscordChatExporter/releases/\n"
            "default: %(default)s"
        ),
    )

    args = parser.parse_args()

    config = load_config(filename=args.config)
    tokens = load_tokens_config(filename=args.tokens)

    return run_all(
        config,
        tokens=tokens,
        executable=args.executable,
        out_dir=args.out,
        config_filename=args.config,
    )


if __name__ == "__main__":
    exit(main())
