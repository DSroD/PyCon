"""Utility functions for minecraft servers."""
from abc import ABC, abstractmethod
from enum import Enum
from typing import override


class _Component(ABC):
    @abstractmethod
    def __str__(self):
        """Returns HTML representation of the component."""


class _Text(_Component):
    def __init__(self, content: str):
        self.content = content

    @override
    def __str__(self):
        return self.content


class _Colored(_Component):
    # TODO: Colors to dict maybe? Or component factory
    class Color(Enum):
        # §0
        BLACK = "black"
        # §1
        DARK_BLUE = "dark_blue"
        # §2
        DARK_GREEN = "dark_green"
        # §3
        DARK_AQUA = "aqua"
        # §4
        DARK_RED = "dark_red"
        # §5
        DARK_PURPLE = "dark_purple"
        # §6
        GOLD = "gold"
        # §7
        GRAY = "gray"
        # §8
        DARK_GRAY = "dark_gray"
        # §9
        BLUE = "blue"
        # §a
        GREEN = "green"
        # §b
        AQUA = "aqua"
        # §c
        RED = "red"
        # §d
        LIGHT_PURPLE = "light_purple"
        # §e
        YELLOW = "yellow"
        # §f
        WHITE = "white"

    def __init__(self, content: _Component, color: Color):
        self.inner = content
        self.color = color

    @override
    def __str__(self):
        return f'<span class="{self.color.value}">{str(self.inner)}</span>'


def bukkit_colored_str_to_html(_: str):
    """
    Creates HTML string with colored text from bukkit color codes.

    :param _: String with bukkit color codes
    :return: HTML string with colored text
    """
    # TODO: implement mapping from color codes (such as §e)
    #       to HTML tags with corresponding color text style
