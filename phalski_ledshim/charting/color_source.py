from typing import Sequence

from .. import ColorSource, Color, Palette
from . import Chart, BinNumber


class ChartSource(ColorSource):

    def __init__(self, pixels: Sequence[int], chart: Chart, *args):
        super().__init__(pixels)
        self._chart = chart
        self._value_sources = args

    def get(self):
        self._chart.set_values(*(s() for s in self._value_sources))
        return self.create_events(self._chart.colors)


class NumBinary(ColorSource):

    def __init__(self, pixels, n: int, fg_color: Color = Palette.WHITE, bg_color: Color = Palette.WHITE.dim(-0.75)):
        super().__init__(pixels)
        self._chart = BinNumber(len(pixels), fg_color, bg_color)
        self._chart.set_values(n)
        self._events = self.create_events(self._chart.colors)

    def get(self):
        return self._events
