"""Utility functions for minecraft servers."""

_formatmap = {
    "l": "bold",
    "m": "strikethrough",
    "n": "underline",
    "o": "italic",
}

_colormap = {
    "0": "black",
    "1": "dark-blue",
    "2": "dark-green",
    "4": "dark-red",
    "3": "dark-aqua",
    "5": "dark-purple",
    "6": "gold",
    "7": "gray",
    "8": "dark-gray",
    "9": "blue",
    "a": "green",
    "b": "aqua",
    "c": "red",
    "d": "light-purple",
    "e": "yellow",
    "f": "white",
}


def _apply_fmt(
        text: str,
        fmts: list[str],
        color: str
) -> str:
    return (f'<span class="{color}{' ' if fmts else ''}{' '.join(fmts)}">' +
            f'{text}</span>') if text else ""


def minecraft_colored_str_to_html(text: str):
    """
    Creates HTML string with colored text from bukkit color codes.

    :param text: String with bukkit color codes
    :return: HTML string with colored text
    """
    # TODO: implement mapping from color codes (such as §e)
    #       to HTML tags with corresponding color text style
    color = _colormap["f"]
    fmts = []
    partial = ""
    result = ""
    nfmt = False  # Next char is format

    for char in text:
        if char == "§":
            nfmt = True
            continue

        if nfmt and char == "r":
            nfmt = False
            result += _apply_fmt(partial, fmts, color)
            color = _colormap["f"]
            fmts.clear()
            partial = ""
            continue

        if nfmt and char in _colormap:
            nfmt = False
            result += _apply_fmt(partial, fmts, color)
            # Color change resets formatting
            # https://minecraft.fandom.com/wiki/Formatting_codes#Usage
            fmts.clear()
            color = _colormap[char]
            partial = ""
            continue

        if nfmt and char in _formatmap:
            nfmt = False
            result += _apply_fmt(partial, fmts, color)
            fmts.append(_formatmap[char])
            partial = ""
            continue

        if nfmt:
            nfmt = False
            partial += f"§{char}"
            continue

        partial += char
    return result + _apply_fmt(partial, fmts, color)
