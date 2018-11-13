import ledshim

from abc import ABC, abstractmethod
from typing import List, Iterable, NamedTuple, Sequence, Set

print(__name__)

class Color:

    def __init__(self, r: int, g: int, b: int, brightness: float = 1.0):
        for s in r, g, b:
            if not 0 <= s <= 255:
                raise ValueError("Illegal saturation value: %d" % s)

        if not 0.0 <= brightness <= 1.0:
            raise ValueError('Illegal brightness value: %f' % brightness)

        self._r = r
        self._g = g
        self._b = b
        self._brightness = brightness

    @property
    def r(self):
        return self._r

    @property
    def g(self):
        return self._g

    @property
    def b(self):
        return self._b

    @property
    def brightness(self):
        return self._brightness

    def adjust_brightness(self, brightness: float = 1.0):
        return Color(self.r, self.g, self.b, brightness)

    def shade(self, f: float):
        if not -1.0 < f < 1.0:
            raise ValueError('Illegal shade factor: %f' % f)

        r = Color.shade_saturation(self.r, f)
        g = Color.shade_saturation(self.g, f)
        b = Color.shade_saturation(self.b, f)

        try:
            return Color(r, g, b, self.brightness)
        except ValueError:
            raise ValueError('Shading not possible for factor: %f' % f)

    def dim(self, f: float):
        if not -1.0 < f < 1.0:
            raise ValueError('Illegal shade factor: %f' % f)

        try:
            return Color(self.r, self.g, self.b, self.brightness * (1 + f))
        except ValueError:
            raise ValueError('Shading not possible for factor: %f' % f)

    @classmethod
    def shade_saturation(cls, s: int, f: float):
        return int(s * (1 + f))

    def __repr__(self):
        return repr((self.r, self.b, self.g, self.brightness))


class Palette:
    """ Basic HTML color palette which can be properly displayed by LEDSHIM
    https://en.wikipedia.org/wiki/Web_colors
    """
    WHITE = Color(255, 255, 255)
    SILVER = Color(191, 191, 191)
    GRAY = Color(127, 127, 127)
    BLACK = Color(0, 0, 0)
    RED = Color(255, 0, 0)
    MAROON = Color(127, 0, 0)
    YELLOW = Color(255, 255, 0)
    OLIVE = Color(127, 127, 0)
    LIME = Color(0, 255, 0)
    GREEN = Color(0, 127, 0)
    AQUA = Color(0, 255, 255)
    TEAL = Color(0, 127, 127)
    BLUE = Color(0, 0, 255)
    NAVY = Color(0, 0, 127)
    FUCHSIA = Color(255, 0, 255)
    PURPLE = Color(127, 0, 127)

    @classmethod
    def colors(cls):
        return [Palette.WHITE, Palette.SILVER, Palette.GRAY, Palette.BLACK, Palette.RED, Palette.MAROON, Palette.YELLOW,
                Palette.OLIVE, Palette.LIME, Palette.GREEN, Palette.AQUA, Palette.TEAL, Palette.BLUE, Palette.NAVY,
                Palette.FUCHSIA, Palette.PURPLE]


ColorChangeEvent = NamedTuple('ColorChangeEvent', [('pixels', Set[int]), ('color', Color)])


class ColorSource(ABC):

    def __init__(self, pixels: Sequence[int]):
        super().__init__()
        self._pixels = pixels

    def create_events(self, colors: Sequence[Color]) -> List[ColorChangeEvent]:
        if not colors:
            return []

        if not len(self._pixels) == len(colors):
            raise ValueError('Illegal count of arguments: expected=%d actual=%d' % (len(self._pixels), len(colors)))

        return [ColorChangeEvent([x], colors[i]) for i, x in enumerate(self._pixels)]

    @abstractmethod
    def get(self) -> List[ColorChangeEvent]:
        pass


class LedShim:

    def __init__(self, brightness: float = 1.0, clear_on_exit: bool = True):
        if not 0 <= brightness <= 1.0:
            raise ValueError("Illegal brightness value: %f" % brightness)

        self._brightness = brightness
        ledshim.set_brightness(brightness)

        self._clear_on_exit = clear_on_exit
        ledshim.set_clear_on_exit(clear_on_exit)

        self._pixels = tuple(range(ledshim.NUM_PIXELS))
        self._state = [Color(0, 0, 0, 0.0)] * ledshim.NUM_PIXELS

    @property
    def pixels(self):
        return self._pixels

    @property
    def state(self):
        return tuple(self._state)

    def apply(self, events: Iterable[ColorChangeEvent], show: bool = False):
        for e in events:
            for x in e.pixels:
                self._state[x] = e.color
                ledshim.set_pixel(x, e.color.r, e.color.g, e.color.b, e.color.brightness)

        if show:
            self.show()

    def show(self):
        ledshim.show()
