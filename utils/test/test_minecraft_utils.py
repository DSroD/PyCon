"""Minecraft utils tests"""
# pylint: disable=missing-class-docstring
import unittest

from utils.minecraft import minecraft_colored_str_to_html


class MinecraftUtilsTest(unittest.TestCase):
    def test_formatting(self):
        """Tests reponse formatting to HTML equivalents"""
        response_from_rcon = "§cX§nY"
        result = minecraft_colored_str_to_html(response_from_rcon)

        self.assertEqual(
            result,
            """<span class="red">X</span><span class="red underline">Y</span>"""
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
