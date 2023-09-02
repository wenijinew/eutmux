#!/usr/bin/env python3
"""Provide utility functions for Tmux option reading and writing."""

import shlex
import subprocess

import yaml
from loguru import logger
from yaml import Loader

UTF_8 = "utf-8"
EMPTY = ""

# tmux options
TMUX_WINDOW_OPTION = "#W"
TMUX_WINDOW_NUMBER_OPTION = "#I"
STYLE_START = "#["
STYLE_END = "]"


class Theme(dict):
    """Wrapper for theme configuration."""

    def __init__(self, theme_config: dict):
        self.status_line = ThemeStatusLine(theme_config)
        self.status_left = ThemeStatusLeft(theme_config)
        self.window = ThemeWindow(theme_config)
        self.status_right = ThemeStatusRight(theme_config)
        super().__init__(
            status_line=self.status_line,
            status_left=self.status_left,
            window=self.window,
            status_right=self.status_right,
        )


class ThemeStatusLine(dict):
    """Wrapper for status_line configuration."""

    def __init__(self, theme_config):
        self.foreground = theme_config["status_line"]["foreground"]
        self.background = theme_config["status_line"]["background"]
        self.left_icon = theme_config["status_line"]["left_icon"]
        self.right_icon = theme_config["status_line"]["right_icong"]
        self.left_decorator = theme_config["status_line"]["left_decorator"]
        self.right_decorator = theme_config["status_line"]["right_decorator"]


class ThemeStatusLeft(dict):
    """Wrapper for status_left configuration."""

    def __init__(self, theme_config):
        """Constructor"""
        status_line = theme_config.get("status_line")
        status_left = theme_config.get("status_left")
        self.fg_option = status_left.get(
            "fg_option", status_line.get("foreground")
        )
        self.bg_option = status_left.get(
            "bg_option", status_line.get("background")
        )
        self.fg_icon = status_left.get(
            "fg_icon", status_line.get("foreground")
        )
        self.bg_icon = status_left.get(
            "bg_icon", status_line.get("background")
        )
        self.fg_decorator = status_left.get(
            "fg_decorator", status_line.get("foreground")
        )
        self.bg_decorator = status_left.get(
            "bg_decorator", status_line.get("background")
        )
        self.icon = status_left.get("icon", status_line.get("left_icon"))
        self.decorator = status_left.get(
            "decorator", status_line.get("left_decorator")
        )


class ThemeWindow(dict):
    """Wrapper for window configuration."""

    def __init__(self, theme_config):
        """Constructor"""
        status_line = theme_config.get("status_line")
        window = theme_config.get("window")
        self.fg_option = window.get("fg_option", status_line.get("foreground"))
        self.bg_option = window.get("bg_option", status_line.get("background"))
        self.fg_icon = window.get("fg_icon", status_line.get("foreground"))
        self.bg_icon = window.get("bg_icon", status_line.get("background"))
        self.fg_decorator = window.get(
            "fg_decorator", status_line.get("foreground")
        )
        self.bg_decorator = window.get(
            "bg_decorator", status_line.get("background")
        )
        self.icon = window.get("icon", status_line.get("left_icon"))
        self.decorator = window.get(
            "decorator", status_line.get("left_decorator")
        )


class ThemeStatusRight(dict):
    """Wrapper for status_right configuration."""

    def __init__(self, theme_config):
        """Constructor"""
        status_line = theme_config.get("status_line")
        status_right = theme_config.get("status_right")
        self.fg_option = status_right.get(
            "fg_option", status_line.get("foreground")
        )
        self.bg_option = status_right.get(
            "bg_option", status_line.get("background")
        )
        self.fg_icon = status_right.get(
            "fg_icon", status_line.get("foreground")
        )
        self.bg_icon = status_right.get(
            "bg_icon", status_line.get("background")
        )
        self.fg_decorator = status_right.get(
            "fg_decorator", status_line.get("foreground")
        )
        self.bg_decorator = status_right.get(
            "bg_decorator", status_line.get("background")
        )
        self.icon = status_right.get("icon", status_line.get("left_icon"))
        self.decorator = status_right.get(
            "decorator", status_line.get("left_decorator")
        )
        self.style = status_right.get("style", status_line.get("style"))


class Constructor:
    """Constructor for status line components."""

    def __init__(self, catppuccin: dict, theme: Theme):
        """Constructor"""
        self.status_left = catppuccin.get("status_left")
        self.window = catppuccin.get("window")
        self.status_right = catppuccin.get("status_right")
        self.theme = theme

    def produce_status_left(self):
        """Produce status left option string"""
        status_left = []
        for options in self.status_left.values():
            enabled = options.get("enabled", "on")
            if not enabled:
                continue
            tmux_option = options.get("tmux_option", EMPTY)
            icon = options.get("icon", self.theme.status_left.get("icon"))
            decorator = options.get(
                "decorator", self.theme.status_left.get("decorator")
            )
            fg_option = options.get(
                "fg_option", self.theme.status_left.get("fg_option")
            )
            bg_option = options.get(
                "bg_option", self.theme.status_left.get("bg_option")
            )
            fg_icon = options.get(
                "fg_icon", self.theme.status_left.get("fg_icon")
            )
            bg_icon = options.get(
                "bg_icon", self.theme.status_left.get("bg_icon")
            )
            fg_decorator = options.get(
                "fg_decorator", self.theme.status_left.get("fg_decorator")
            )
            bg_decorator = options.get(
                "bg_decorator", self.theme.status_left.get("bg_decorator")
            )
            style = options.get("style", self.theme.status_left.get("style"))
            tmux_option_style = (
                f"{self.get_style(fg_option, bg_option, style)}"
            )
            icon_style = f"{self.get_style(fg_icon, bg_icon, style)}"
            decorator_style = (
                f"{self.get_style(fg_decorator, bg_decorator, style)}"
            )
            tmux_option = f"{tmux_option_style}{tmux_option}"
            icon = f"{icon_style}{icon}"
            decorator = f"{decorator_style}{decorator}"
            component_value = f"{icon}{decorator}{tmux_option}"
            status_left.append(component_value)

        return " ".join(status_left)

    def produce_window(self):
        """Return tuple with active window and inactive window option strings"""
        active_window = None
        inactive_window = None
        for component, options in self.window.items():
            icon = options.get("icon", self.theme.window.get("icon"))
            decorator = options.get(
                "decorator", self.theme.window.get("decorator")
            )
            fg_window = options.get(
                "fg_window", self.theme.window.get("fg_window")
            )
            bg_window = options.get(
                "bg_window", self.theme.window.get("bg_window")
            )
            fg_number = options.get(
                "fg_number", self.theme.window.get("fg_number")
            )
            bg_number = options.get(
                "bg_number", self.theme.window.get("bg_number")
            )
            fg_icon = options.get("fg_icon", self.theme.window.get("fg_icon"))
            bg_icon = options.get("bg_icon", self.theme.window.get("bg_icon"))
            fg_decorator = options.get(
                "fg_decorator", self.theme.window.get("fg_decorator")
            )
            bg_decorator = options.get(
                "bg_decorator", self.theme.window.get("bg_decorator")
            )
            style = options.get("style", self.theme.window.get("style"))
            window_style = f"{self.get_style(fg_window, bg_window, style)}"
            window_number_style = (
                f"{self.get_style(fg_number, bg_number, style)}"
            )
            icon_style = f"{self.get_style(fg_icon, bg_icon, style)}"
            decorator_style = (
                f"{self.get_style(fg_decorator, bg_decorator, style)}"
            )
            window = f"{window_style}{TMUX_WINDOW_OPTION}"
            window_number = f"{window_number_style}{TMUX_WINDOW_NUMBER_OPTION}"
            icon = f"{icon_style}{icon}"
            decorator = f"{decorator_style}{decorator}"
            component_value = f"{window}{window_number}{icon}{decorator}"
            if component == "active":
                active_window = component_value
            else:
                inactive_window = component_value

        return active_window, inactive_window

    def produce_status_right(self):
        """Produce status right tmux options string."""
        status_right = []
        for options in self.status_right.values():
            enabled = options.get("enabled", "on")
            if not enabled:
                continue
            tmux_option = options.get("tmux_option", EMPTY)
            icon = options.get("icon", self.theme.status_right.get("icon"))
            decorator = options.get(
                "decorator", self.theme.status_right.get("decorator")
            )
            fg_option = options.get(
                "fg_option", self.theme.status_right.get("fg_option")
            )
            bg_option = options.get(
                "bg_option", self.theme.status_right.get("bg_option")
            )
            fg_icon = options.get(
                "fg_icon", self.theme.status_right.get("fg_icon")
            )
            bg_icon = options.get(
                "bg_icon", self.theme.status_right.get("bg_icon")
            )
            fg_decorator = options.get(
                "fg_decorator", self.theme.status_right.get("fg_decorator")
            )
            bg_decorator = options.get(
                "bg_decorator", self.theme.status_right.get("bg_decorator")
            )
            style = options.get("style", self.theme.status_right.get("style"))
            tmux_option_style = (
                f"{self.get_style(fg_option, bg_option, style)}"
            )
            icon_style = f"{self.get_style(fg_icon, bg_icon, style)}"
            decorator_style = (
                f"{self.get_style(fg_decorator, bg_decorator, style)}"
            )
            tmux_option = f"{tmux_option_style}{tmux_option}"
            icon = f"{icon_style}{icon}"
            decorator = f"{decorator_style}{decorator}"
            component_value = f"{decorator}{icon}{tmux_option}"
            status_right.append(component_value)

        return " ".join(status_right)

    def get_style(self, foreground, background, style):
        """construct style string with foreground and background"""
        pieces = []
        if foreground:
            pieces.append(f"fg={foreground}")
        if background:
            pieces.append(f"bg={background}")
        pieces.append(style)
        return f"{STYLE_START}{','.join(pieces)}{STYLE_END}"

    def produce_option_command(self, option, value):
        """Return tmux set option command"""
        return f"set-option {option} {value}"

    def produce_option_commands(self):
        """Return all tmux set option commands."""
        status_left = self.produce_status_left()
        active_window, inactive_window = self.produce_window()
        status_right = self.produce_status_right()
        status_left_cmd = self.produce_option_command(
            "status-left", status_left
        )
        active_window_cmd = self.produce_option_command(
            "window-status-format", active_window
        )
        inactive_window_cmd = self.produce_option_command(
            "window-status-current-format", inactive_window
        )
        status_right_cmd = self.produce_option_command(
            "status-right", status_right
        )
        option_commands = []
        option_commands.append(status_left_cmd)
        option_commands.append(active_window_cmd)
        option_commands.append(inactive_window_cmd)
        option_commands.append(status_right_cmd)
        return ";".join(option_commands)


def main(config_file="catppuccin.yaml"):
    """Load config file, overwrite options by value from tmux.conf."""
    # TODO: the config file should be customizable by putting under
    # $HOME/.tmux/catppuccin.yaml
    with open(config_file, "r", encoding=UTF_8) as config:
        catppuccin = yaml.load(config, Loader=Loader)

        theme_name = catppuccin.get("theme")
        theme_config = yaml.load(f"{theme_name}.theme.yaml", Loader=Loader)
        theme = Theme(theme_config)

        constructor = Constructor(catppuccin, theme)
        tmux_commands = constructor.produce_option_commands()

    final_tmux_command = f"tmux {tmux_commands}"
    run_shell_command(final_tmux_command)


def get_tmux_option(option_name, default_value):
    """Read tmux option."""
    assert option_name is not None, "option_name is None!"
    assert default_value is not None, "default_value is None!"

    if not option_name.startswith("@"):
        option_name = f"@{option_name}"
    shell_cmd = f'tmux show_option _gqv "{option_name}"'
    return run_shell_command(shell_cmd, default_value)


def run_shell_command(command, default_output=None):
    """Run shell command."""
    try:
        command_args = shlex.split(command)
        value = subprocess.check_output(command_args, shell=False).decode(
            UTF_8
        )
        return value
    except Exception:
        logger.opt(exception=True).debug(
            f"{command} is failed to run. use default value: \
                                         {default_output} as output."
        )
        return default_output


if __name__ == "__main__":
    main()