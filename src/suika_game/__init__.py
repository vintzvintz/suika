"""Suika Game - A watermelon physics puzzle game.

This package contains the complete Suika Game implementation using
pyglet for graphics and pymunk for 2D physics simulation.
"""

__version__ = "1.0.0"
__author__ = "Vincent"

from .game import SuikaWindow
from .main import main

__all__ = ["SuikaWindow", "main"]