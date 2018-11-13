import enum
import typing

__all__ = ['MAX_DEPTH_BITS', 'MAX_BRIGHTNESS', 'Color', 'ColorDepth', 'color_for', 'encode', 'set_brightness', 'dim', 'shade',
           'WHITE', 'SILVER', 'GRAY', 'BLACK', 'RED', 'MAROON', 'YELLOW', 'OLIVE', 'LIME', 'GREEN', 'AQUA', 'TEAL',
           'BLUE', 'NAVY', 'FUCHSIA', 'PURPLE']


def _max_color_value(bits: int):
    return (1 << bits) - 1


MAX_DEPTH_BITS = 8  # LED SHIM does not support a higher depth
MAX_BRIGHTNESS = 1.0  # LED SHIM brightness is a value between 0.0 and 1.0


class DepthMapper:

    def __init__(self, max_bits: int):
        if 0 > max_bits or MAX_DEPTH_BITS > max_bits:
            raise ValueError('Illegal max_bits value: %d' % max_bits)

        n_values = 1 << max_bits

        maps = [((-1,), (-1,))] * max_bits
        for b in range(max_bits):
            b_max = _max_color_value(b + 1)
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


DEPTH_MAPPER = DepthMapper(MAX_DEPTH_BITS)  # init static mapping tables


class ColorDepth(enum.Enum):
    """An enumeration of color depth encodings"""
    BIT8 = (3, 3, 2)  # 8-bit
    BIT15 = (5, 5, 5)  # HighColor
    BIT16 = (5, 6, 5)  # HighColor alt.
    BIT24 = (8, 8, 8)  # TrueColor highest possible for LED SHIM

    def __init__(self, r: int, g: int, b: int):
        """

        :param r: Red color channel depth in bits
        :param g: Green color channel depth in bits
        :param b: Blue color channel depth in bits
        """
        self.r = r
        self.g = g
        self.b = b
        self.r_max, self.g_max, self.b_max = [_max_color_value(n) for n in [r, g, b]]


MAX_DEPTH = ColorDepth.BIT24


class Color(typing.NamedTuple('Color', (('r', int), ('g', int), ('b', int), ('brightness', float),
                                        ('depth', ColorDepth)))):
    """Color representation for ledshim colors

    Depth is only virtual, narrowing the available colors within the 8-bit channel
    """


def color_for(r: int, g: int, b: int, brightness: float = MAX_BRIGHTNESS, depth=MAX_DEPTH) -> Color:
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
        red = DEPTH_MAPPER.get_value(r, depth.r, MAX_DEPTH.r)
        green = DEPTH_MAPPER.get_value(g, depth.g, MAX_DEPTH.g)
        blue = DEPTH_MAPPER.get_value(b, depth.b, MAX_DEPTH.b)
    except IndexError as e:
        raise ValueError("Illegal color component value for depth: r=%d, g=%d, b=%d, depth=%s" % (r, g, b, depth))

    if 0.0 > brightness or brightness > MAX_BRIGHTNESS:
        raise ValueError('Illegal brightness value: %f' % brightness)

    return Color(red, green, blue, brightness, depth)


def encode(color: Color, depth: ColorDepth) -> Color:
    return color._replace(
        r=DEPTH_MAPPER.get_value(color.r, MAX_DEPTH.r, depth.r),
        g=DEPTH_MAPPER.get_value(color.g, MAX_DEPTH.g, depth.g),
        b=DEPTH_MAPPER.get_value(color.b, MAX_DEPTH.b, depth.b),
        depth=depth)


def set_brightness(color: Color, brightness: float = 1.0) -> Color:
    return color._replace(brightness=brightness)


def dim(color: Color, f: float) -> Color:
    if 0.0 > f:
        raise ValueError('Negative dim factor: %f' % f)

    return color._replace(brightness=min(color.brightness * f, MAX_BRIGHTNESS))


def shade(color: Color, f: float) -> Color:
    if 0.0 > f:
        raise ValueError('Negative shade factor: %f' % f)

    r, g, b = (int(c * f) for c in (color.r, color.g, color.b))

    try:
        # RGB values are in max_depth so we have to create a new color at max_depth and encode it back to color depth
        return encode(color(r, g, b, color.brightness), color.depth)
    except ValueError:
        raise ValueError('Component overflow. Shading not possible for factor: %f' % f)


# Basic HTML color palette which can be properly displayed by LEDSHIM (https://en.wikipedia.org/wiki/Web_colors)
WHITE = color_for(255, 255, 255)
SILVER = color_for(191, 191, 191)
GRAY = color_for(127, 127, 127)
BLACK = color_for(0, 0, 0)
RED = color_for(255, 0, 0)
MAROON = color_for(127, 0, 0)
YELLOW = color_for(255, 255, 0)
OLIVE = color_for(127, 127, 0)
LIME = color_for(0, 255, 0)
GREEN = color_for(0, 127, 0)
AQUA = color_for(0, 255, 255)
TEAL = color_for(0, 127, 127)
BLUE = color_for(0, 0, 255)
NAVY = color_for(0, 0, 127)
FUCHSIA = color_for(255, 0, 255)
PURPLE = color_for(127, 0, 127)
