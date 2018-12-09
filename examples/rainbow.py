import time
import colorsys

from typing import Sequence

from phalski_ledshim import app, client, color


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


if __name__ == '__main__':
    a = app.App()
    a.configure_worker([Rainbow(a.pixels, 60)], 0.1)
    a.exec()
