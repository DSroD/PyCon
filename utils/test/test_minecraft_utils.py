"""Minecraft utils tests"""
# pylint: disable=missing-class-docstring
import unittest

from utils.minecraft import minecraft_colored_str_to_html


class MinecraftUtilsTest(unittest.TestCase):
    def test_formatting(self):
        """Tests reponse formatting to HTML equivalents"""
        response_from_rcon = "§cX§nY§lZ"
        result = minecraft_colored_str_to_html(response_from_rcon)

        self.assertEqual(
            result,
            """<span class="red">X</span><span class="red underline">Y</span><span class="red underline bold">Z</span>"""  # pylint: disable=line-too-long
        )

    def test_formatting_color_resets(self):
        """
        Tests color format resets other formats.

        https://minecraft.fandom.com/wiki/Formatting_codes#Usage
        """
        response_from_rcon = "§nX§cY"
        result = minecraft_colored_str_to_html(response_from_rcon)

        self.assertEqual(
            result,
            """<span class="white underline">X</span><span class="red">Y</span>"""
        )

    def test_formatting_reset(self):
        """Tests reset sequence resets formatting and color."""
        response_from_rcon = "§c§nX§rY"
        result = minecraft_colored_str_to_html(response_from_rcon)

        self.assertEqual(
            result,
            """<span class="red underline">X</span><span class="white">Y</span>"""
        )
