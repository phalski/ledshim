from __future__ import absolute_import

import abc
import ledshim

from typing import NamedTuple, List, Sequence

from phalski_ledshim import color

__all__ = ['Factory']


class ChangeEvent(NamedTuple('ChangeEvent', [('pixels', List[int]), ('color', color.Color)])):
    """Pixel status change event

    Defines a new color for one or more pixels.
    """


class Client:
    """Client encapsulating all ledshim operations

    The client exports a subset of the original ledshim driver object api
    """

    def __init__(self, brightness: float = color.Factory.MAX_BRIGHTNESS, clear_on_exit: bool = True,
                 depth: color.Depth = color.Depth.BIT24):
        self.brightness = 0.0
        self.clear_on_exit = True
        self.depth = depth
        self.pixels = list(range(ledshim.NUM_PIXELS))
        self.state = [color.Factory.color(0, 0, 0, 0.0, self.depth)] * ledshim.NUM_PIXELS

        self.set_brightness(brightness)
        self.set_clear_on_exit(clear_on_exit)

    def apply_changes(self, changes: Sequence[ChangeEvent]):
        for c in changes:
            for x in c.pixels:
                self.set_pixel(x, c.color)

    def set_clear_on_exit(self, value: bool = True):
        self.clear_on_exit = value
        ledshim.set_clear_on_exit(value)

    def set_brightness(self, brightness: float):
        if 0 > brightness or brightness > color.Factory.MAX_BRIGHTNESS:
            raise ValueError("Illegal brightness value: %f" % brightness)

        self.brightness = brightness
        ledshim.set_brightness(brightness)

    def set_pixel(self, x: int, c: color.Color):
        c = color.Factory.encode(c, self.depth)
        self.state[x] = c
        ledshim.set_pixel(x, c.r, c.g, c.b, c.brightness)

    def set_all(self, c: color.Color):
        c = color.Factory.encode(c, self.depth)
        ledshim.set_all(c.r, c.g, c.b, c.brightness)

    def clear(self):
        self.state = [color.Factory.color(0, 0, 0, 0.0, self.depth)] * ledshim.NUM_PIXELS
        ledshim.clear()

    def show(self):
        ledshim.show()


class Factory(abc.ABC):

    @classmethod
    def client(cls,
               brightness: float = color.Factory.MAX_BRIGHTNESS,
               clear_on_exit: bool = True,
               depth: color.Depth = color.Depth.BIT24) -> Client:
        return Client(brightness, clear_on_exit, depth)

    @classmethod
    def change_event(cls, pixel_color: color.Color, *args: int):
        return ChangeEvent(list(args), pixel_color)
