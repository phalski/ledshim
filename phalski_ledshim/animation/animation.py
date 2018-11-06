import colorsys
import time

from typing import Sequence

from .. import Color, ColorChangeEvent, ColorSource


class Rainbow(ColorSource):

    def __init__(self, pixels: Sequence[int], num_colors: int = 16, speed: float = 1.0):
        super().__init__(pixels)
        if not 0 < num_colors:
            raise ValueError('num_colors must be greater than 0: %d' % num_colors)

        if not 0 < speed:
            raise ValueError('speed must be greater than 0: %d' % speed)

        self._spacing = 360.0 / num_colors
        self._speed =speed

    def get(self):
        hue = int(time.time() * 100 * self._speed) % 360

        def rainbow_event(i: int, x: int):
            offset = i * self._spacing
            h = ((hue + offset) % 360) / 360.0
            r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(h, 1.0, 1.0)]
            return ColorChangeEvent([x], Color(r, g, b))

        return [rainbow_event(i, x) for i, x in enumerate(self._pixels)]
