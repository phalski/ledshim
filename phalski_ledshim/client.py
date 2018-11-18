import abc
import ledshim
import typing

from .color import Color, ColorDepth, ColorFactory


class ChangeEvent(typing.NamedTuple('ChangeEvent', [('pixels', typing.Tuple[int]), ('color', Color)])):
    """"""


class ChangeEventFactory(abc.ABC):

    @classmethod
    def change_for(cls, c: Color, pixel: int, *args: int) -> ChangeEvent:
        pixels = pixel,
        return ChangeEvent(pixels + args, c)


class Client:
    """Client encapsulating all ledshim operations

    The client does export a subset of the original ledshim driver object api
    """

    def __init__(self, brightness: float = ColorFactory.MAX_BRIGHTNESS, clear_on_exit: bool = True,
                 depth: ColorDepth = ColorDepth.BIT24):
        self._brightness = 0.0
        self._clear_on_exit = True
        self._depth = depth
        self._pixels = tuple(range(ledshim.NUM_PIXELS))
        self._state = [ColorFactory.color_for(0, 0, 0, 0.0, self._depth)] * ledshim.NUM_PIXELS

        self.set_brightness(brightness)
        self.set_clear_on_exit(clear_on_exit)

    @property
    def pixels(self) -> typing.Tuple[int]:
        return self._pixels

    @property
    def state(self) -> typing.Tuple[Color]:
        return tuple(self._state)

    def apply_changes(self, changes: typing.Sequence[ChangeEvent]):
        for c in changes:
            for x in c.pixels:
                self.set_pixel(x, c.color)

    def set_clear_on_exit(self, value: bool = True):
        self._clear_on_exit = value
        ledshim.set_clear_on_exit(value)

    def set_brightness(self, brightness: float):
        if 0 > brightness or brightness > ColorFactory.MAX_BRIGHTNESS:
            raise ValueError("Illegal brightness value: %f" % brightness)

        self._brightness = brightness
        ledshim.set_brightness(brightness)

    def set_pixel(self, x: int, c: Color):
        c = ColorFactory.encode(c, self._depth)
        self._state[x] = c
        ledshim.set_pixel(x, c.r, c.g, c.b, c.brightness)

    def set_all(self, c: Color):
        c = ColorFactory.encode(c, self._depth)
        ledshim.set_all(c.r, c.g, c.b, c.brightness)

    def clear(self):
        self._state = [ColorFactory.color_for(0, 0, 0, 0.0, self._depth)] * ledshim.NUM_PIXELS
        ledshim.clear()

    def show(self):
        ledshim.show()
