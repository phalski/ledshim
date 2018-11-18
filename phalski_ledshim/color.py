import abc
import enum
import typing

__all__ = ['Color', 'ColorDepth', 'ColorFactory', 'NamedColor']


class ColorDepth(enum.Enum):
    """An enumeration of color depth encodings"""
    BIT8 = (3, 3, 2)  # 8-bit
    BIT15 = (5, 5, 5)  # HighColor
    BIT16 = (5, 6, 5)  # HighColor alt.
    BIT24 = (8, 8, 8)  # TrueColor highest possible for LED SHIM

    @classmethod
    def max_depth(cls):
        return ColorDepth.BIT24

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


class DepthMapper:

    def __init__(self, max_bits: int = ColorDepth.max_depth_bits()):
        if 0 > max_bits or ColorDepth.max_depth_bits() > max_bits:
            raise ValueError('Illegal max_bits value: %d' % max_bits)

        n_values = 1 << max_bits

        maps = [((-1,), (-1,))] * max_bits
        for b in range(max_bits):
            b_max = ColorDepth.max_color_value(b + 1)
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


class Color(typing.NamedTuple('Color', (('r', int), ('g', int), ('b', int), ('brightness', float),
                                        ('depth', ColorDepth)))):
    """Color representation for ledshim colors

    Depth is only virtual, narrowing the available colors within the 8-bit channel
    """
    pass


class ColorFactory(abc.ABC):
    MAX_BRIGHTNESS = 1.0  # LED SHIM brightness is a value between 0.0 and 1.0
    DEPTH_MAPPER = DepthMapper()  # init static mapping tables

    @classmethod
    def color_for(cls, r: int, g: int, b: int, brightness: float = MAX_BRIGHTNESS,
                  depth=ColorDepth.max_depth()) -> Color:
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
            red = ColorFactory.DEPTH_MAPPER.get_value(r, depth.r, ColorDepth.max_depth().r)
            green = ColorFactory.DEPTH_MAPPER.get_value(g, depth.g, ColorDepth.max_depth().g)
            blue = ColorFactory.DEPTH_MAPPER.get_value(b, depth.b, ColorDepth.max_depth().b)
        except IndexError as e:
            raise ValueError("Illegal color component value for depth: r=%d, g=%d, b=%d, depth=%s" % (r, g, b, depth),
                             e)

        if 0.0 > brightness or brightness > ColorFactory.MAX_BRIGHTNESS:
            raise ValueError('Illegal brightness value: %f' % brightness)

        return Color(red, green, blue, brightness, depth)

    @classmethod
    def encode(cls, color: Color, depth: ColorDepth) -> Color:
        return color._replace(
            r=ColorFactory.DEPTH_MAPPER.get_value(color.r, ColorDepth.max_depth().r, depth.r),
            g=ColorFactory.DEPTH_MAPPER.get_value(color.g, ColorDepth.max_depth().g, depth.g),
            b=ColorFactory.DEPTH_MAPPER.get_value(color.b, ColorDepth.max_depth().b, depth.b),
            depth=depth)

    @classmethod
    def set_brightness(cls, color: Color, brightness: float = 1.0) -> Color:
        return color._replace(brightness=brightness)

    @classmethod
    def dim(cls, color: Color, f: float) -> Color:
        if 0.0 > f:
            raise ValueError('Negative dim factor: %f' % f)

        return color._replace(brightness=min(color.brightness * f, ColorFactory.MAX_BRIGHTNESS))

    @classmethod
    def shade(cls, color: Color, f: float) -> Color:
        if 0.0 > f:
            raise ValueError('Negative shade factor: %f' % f)

        r, g, b = (int(c * f) for c in (color.r, color.g, color.b))

        try:
            # RGB values are in max_depth so we have to create a new color at max_depth and map it back to color depth
            return ColorFactory.encode(ColorFactory.color_for(r, g, b, color.brightness), color.depth)
        except ValueError:
            raise ValueError('Component overflow. Shading not possible for factor: %f' % f)


class NamedColor(abc.ABC):
    # Basic HTML color palette which can be properly displayed by LEDSHIM (https://en.wikipedia.org/wiki/Web_colors)
    WHITE = ColorFactory.color_for(255, 255, 255)
    SILVER = ColorFactory.color_for(191, 191, 191)
    GRAY = ColorFactory.color_for(127, 127, 127)
    BLACK = ColorFactory.color_for(0, 0, 0)
    RED = ColorFactory.color_for(255, 0, 0)
    MAROON = ColorFactory.color_for(127, 0, 0)
    YELLOW = ColorFactory.color_for(255, 255, 0)
    OLIVE = ColorFactory.color_for(127, 127, 0)
    LIME = ColorFactory.color_for(0, 255, 0)
    GREEN = ColorFactory.color_for(0, 127, 0)
    AQUA = ColorFactory.color_for(0, 255, 255)
    TEAL = ColorFactory.color_for(0, 127, 127)
    BLUE = ColorFactory.color_for(0, 0, 255)
    NAVY = ColorFactory.color_for(0, 0, 127)
    FUCHSIA = ColorFactory.color_for(255, 0, 255)
    PURPLE = ColorFactory.color_for(127, 0, 127)
