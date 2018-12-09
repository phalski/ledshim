import abc
import enum
from typing import NamedTuple

__all__ = ['Depth', 'Factory', 'NamedColor']


class Depth(enum.Enum):
    """An enumeration of color depth encodings"""
    BIT8 = (3, 3, 2)  # 8-bit
    BIT15 = (5, 5, 5)  # HighColor
    BIT16 = (5, 6, 5)  # HighColor alt.
    BIT24 = (8, 8, 8)  # TrueColor highest possible for LED SHIM

    @classmethod
    def max_depth(cls):
        return Depth.BIT24

    @classmethod
    def max_depth_bits(cls):
        return 8  # LED SHIM does not support a higher depth

    @classmethod
    def max_color_value(cls, bits: int):
        return (1 << bits) - 1

    def __init__(self, r: int, g: int, b: int):
        """

        :param r: Red color channel depth in bits
        :param g: Green color channel depth in bits
        :param b: Blue color channel depth in bits
        """
        self.r = r
        self.g = g
        self.b = b
        self.r_max, self.g_max, self.b_max = [self.max_color_value(n) for n in [r, g, b]]


class DepthMapper(object):

    def __init__(self, max_bits: int = Depth.max_depth_bits()):
        if 0 > max_bits or Depth.max_depth_bits() > max_bits:
            raise ValueError('Illegal max_bits value: %d' % max_bits)

        n_values = 1 << max_bits

        maps = [((-1,), (-1,))] * max_bits
        for b in range(max_bits):
            b_max = Depth.max_color_value(b + 1)
            depth_to_max_depth = [-1] * n_values
            for v in range(n_values):
                spacing = (n_values - 1) / b_max
                depth_to_max_depth[v] = round(round(v / spacing) * spacing)

            max_depth_to_depth = sorted(set(depth_to_max_depth))
            maps[b] = tuple(depth_to_max_depth), tuple(max_depth_to_depth)

        self._max_bits = max_bits
        self._maps = tuple(maps)

    def get_value(self, v: int, source_depth_bits: int, target_depth_bits: int):
        try:
            mappings = self._maps[source_depth_bits - 1]
        except IndexError as e:
            raise ValueError('No mappings found for: source_depth=%d' % source_depth_bits, e)

        try:
            v_max_depth = mappings[1][v]
        except IndexError as e:
            raise ValueError('No mapping found for value=%d' % v, e)

        if self._max_bits == target_depth_bits:
            return v_max_depth

        try:
            return self._maps[target_depth_bits - 1][0][v_max_depth]
        except IndexError as e:
            raise ValueError('No mapping found for: target_depth=%d' % target_depth_bits, e)


class Color(NamedTuple('Color', (('r', int), ('g', int), ('b', int), ('brightness', float),
                                        ('depth', Depth)))):
    """Color representation for ledshim colors

    Depth is only virtual, narrowing the available colors within the 8-bit channel
    """
    pass


class Factory(abc.ABC):
    MAX_BRIGHTNESS = 1.0  # LED SHIM brightness is a value between 0.0 and 1.0
    DEPTH_MAPPER = DepthMapper()  # init static mapping tables

    @classmethod
    def color(cls, r: int, g: int, b: int, brightness: float = MAX_BRIGHTNESS,
              depth=Depth.max_depth()) -> Color:
        """Creates a new 24-bit LedColor for the given args

        Main factory function for colors. Allows only valid values for the named tuple.

        :param r: The 8-bit red saturation value for this color (max depends on the depth setting)
        :param g: The 8-bit green saturation value for this color (max depends on the depth setting)
        :param b: The 8-bit blue saturation value for this color (max depends on the depth setting)
        :param brightness: The brightness value as float between 0.0 and 1.0
        :param depth: The depth setting for color encoding
        :raises ValueError: If color saturation or brightness values are not allowed
        :return: The new and valid LedColor
        """
        try:
            red = Factory.DEPTH_MAPPER.get_value(r, depth.r, Depth.max_depth().r)
            green = Factory.DEPTH_MAPPER.get_value(g, depth.g, Depth.max_depth().g)
            blue = Factory.DEPTH_MAPPER.get_value(b, depth.b, Depth.max_depth().b)
        except IndexError as e:
            raise ValueError("Illegal color component value for depth: r=%d, g=%d, b=%d, depth=%s" % (r, g, b, depth),
                             e)

        if 0.0 > brightness or brightness > Factory.MAX_BRIGHTNESS:
            raise ValueError('Illegal brightness value: %f' % brightness)

        return Color(red, green, blue, brightness, depth)

    @classmethod
    def encode(cls, color: Color, depth: Depth) -> Color:
        return color._replace(
            r=Factory.DEPTH_MAPPER.get_value(color.r, Depth.max_depth().r, depth.r),
            g=Factory.DEPTH_MAPPER.get_value(color.g, Depth.max_depth().g, depth.g),
            b=Factory.DEPTH_MAPPER.get_value(color.b, Depth.max_depth().b, depth.b),
            depth=depth)

    @classmethod
    def set_brightness(cls, color: Color, brightness: float = 1.0) -> Color:
        return color._replace(brightness=brightness)

    @classmethod
    def dim(cls, color: Color, f: float) -> Color:
        if 0.0 > f:
            raise ValueError('Negative dim factor: %f' % f)

        return color._replace(brightness=min(color.brightness * f, Factory.MAX_BRIGHTNESS))

    @classmethod
    def shade(cls, color: Color, f: float) -> Color:
        if 0.0 > f:
            raise ValueError('Negative shade factor: %f' % f)

        r, g, b = (int(c * f) for c in (color.r, color.g, color.b))

        try:
            # RGB values are in max_depth so we have to create a new color at max_depth and map it back to color depth
            return Factory.encode(Factory.color(r, g, b, color.brightness), color.depth)
        except ValueError:
            raise ValueError('Component overflow. Shading not possible for factor: %f' % f)


class NamedColor(abc.ABC):
    # Basic HTML color palette which can be properly displayed by LEDSHIM (https://en.wikipedia.org/wiki/Web_colors)
    WHITE = Factory.color(255, 255, 255)
    SILVER = Factory.color(191, 191, 191)
    GRAY = Factory.color(127, 127, 127)
    BLACK = Factory.color(0, 0, 0)
    RED = Factory.color(255, 0, 0)
    MAROON = Factory.color(127, 0, 0)
    YELLOW = Factory.color(255, 255, 0)
    OLIVE = Factory.color(127, 127, 0)
    LIME = Factory.color(0, 255, 0)
    GREEN = Factory.color(0, 127, 0)
    AQUA = Factory.color(0, 255, 255)
    TEAL = Factory.color(0, 127, 127)
    BLUE = Factory.color(0, 0, 255)
    NAVY = Factory.color(0, 0, 127)
    FUCHSIA = Factory.color(255, 0, 255)
    PURPLE = Factory.color(127, 0, 127)
