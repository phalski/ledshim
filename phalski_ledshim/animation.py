from __future__ import absolute_import

import colorsys
import time

from typing import Sequence

from phalski_ledshim import color, app


class Rainbow(app.InfiniteColorSource):

    def __init__(self, pixels: Sequence[int], num_colors: int = 16, speed: float = 1.0):
        super().__init__(pixels)
        if not 0 < num_colors:
            raise ValueError('num_colors must be greater than 0: %d' % num_colors)

        if not 0 < speed:
            raise ValueError('speed must be greater than 0: %d' % speed)

        self._spacing = 360.0 / num_colors
        self._speed = speed

    def get_colors(self, num_pixels: int):
        hue = int(time.time() * 100 * self._speed) % 360

        def get_color(i: int):
            offset = i * self._spacing
            h = ((hue + offset) % 360) / 360.0
            r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(h, 1.0, 1.0)]
            return color.Factory.color(r, g, b)

        return {i: get_color(i) for i in range(num_pixels)}


class LedTest(app.ColorSource):

    def __init__(self, pixels: Sequence[int]):
        super().__init__(pixels, True)

    def colors(self, num_pixels: int):
        for c in [color.Factory.color(255, 0, 0), color.Factory.color(0, 255, 0),
                  color.Factory.color(0, 0, 255)]:
            for i in range(num_pixels):
                yield {i: c}
