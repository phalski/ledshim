from __future__ import absolute_import

import abc

from typing import Callable, Dict, NamedTuple, Optional, Sequence, Tuple

from phalski_ledshim import color, app

__all__ = ['Chart', 'Factory']


class ValueSpecification(NamedTuple('ValueSpecification',
                                    [('min', float), ('max', float), ('is_capped', bool), ('is_normalised', bool)])):

    def apply(self, value: float):
        if value < self.min:
            if self.is_capped:
                value = self.min
            else:
                raise ValueError('value %f is lower than specified min %f' % (value, self.min))
        elif self.max < value:
            if self.is_capped:
                value = self.max
            else:
                raise ValueError('value %f is greater than specified max %f' % (value, self.max))

        return self.normalize(value) if self.is_normalised else value

    def normalize(self, value: float) -> float:
        return (value - self.min) / (self.max - self.min)


class Chart(abc.ABC):

    def __init__(self, length: int, fg_color: color.Color, bg_color: color.Color, *args: ValueSpecification):
        self.colors = [color.NamedColor.BLACK] * length
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.value_specs = args

    def validate_and_process_values(self, *args: float):
        num_specs = len(self.value_specs)
        num_values = len(args)
        if not num_specs == num_values:
            raise ValueError('Illegal number of values: expected=%d actual=%d' % (num_specs, num_values))

        value_list = list(args)
        for i, spec in enumerate(self.value_specs):
            try:
                value_list[i] = spec.apply(value_list[i])
            except ValueError as e:
                raise ValueError('Failed to process value %d=%f' % (i, value_list[i]), e)

        return tuple(value_list)

    def set_values(self, *args: float):
        values = self.validate_and_process_values(*args)
        return self.apply_values(*values)

    @abc.abstractmethod
    def apply_values(self, *args: float):
        pass


class BarChart(Chart):

    def __init__(self, length: int, fg_color: color.Color, bg_color: color.Color, spec: ValueSpecification):
        super().__init__(length, fg_color, bg_color, Factory.spec_normalized(spec))

    def apply_values(self, *args: float):
        v, = args
        v *= len(self.colors)

        for i in range(len(self.colors)):
            self.colors[i] = self.bg_color if v <= 0 else color.Factory.shade(self.fg_color, min(v, 1.0))
            v -= 1


class RedBlueBarChart(Chart):

    def __init__(self, length: int, red: ValueSpecification, blue: ValueSpecification, brightness: float,
                 bg_shade: float):
        c = color.Factory.color(255, 0, 255, brightness)
        super().__init__(length, c, color.Factory.shade(c, bg_shade), Factory.spec_normalized(red),
                         Factory.spec_normalized(blue))

    def apply_values(self, *args: float):
        red, blue = (len(self.colors) * v for v in args)

        for i in range(len(self.colors)):
            r = self.bg_color.r if red <= 0 else int(self.fg_color.r * min(red, 1.0))
            b = self.bg_color.b if blue <= 0 else int(self.fg_color.b * min(blue, 1.0))
            self.colors[i] = color.Factory.color(r, 0, b, self.fg_color.brightness)

            red -= 1
            blue -= 1


class BinNumber(Chart):

    def __init__(self, length: int, capped: bool, fg_color: color.Color, bg_color: color.Color):
        super().__init__(length, fg_color, bg_color, Factory.spec(0.0, (1 << length) - 1, capped, False))

    def apply_values(self, *args: float):
        v, = args
        n = int(v)

        for i in range(len(self.colors)):
            self.colors[i] = self.fg_color if 0 < 1 << i & n else self.bg_color


class RedBlueBinNumber(Chart):

    def __init__(self, length: int, capped: bool, brightness: float, bg_shade: float):
        c = color.Factory.color(255, 0, 255, brightness)
        s = Factory.spec(0.0, (1 << length) - 1, capped, False)
        super().__init__(length, c, color.Factory.shade(c, bg_shade), s, s)

    def apply_values(self, *args: float):
        red, blue = (int(v) for v in args)

        for i in range(len(self.colors)):
            r = self.fg_color.r if 0 < 1 << i & red else self.bg_color.r
            b = self.fg_color.b if 0 < 1 << i & blue else self.bg_color.b
            self.colors[i] = color.Factory.color(r, 0, b, self.fg_color.brightness)


class SingleStat(Chart):

    def __init__(self, length: int, spec: ValueSpecification, default_color: color.Color,
                 *args: Tuple[float, color.Color]):
        super().__init__(length, default_color, default_color, spec)
        self.color_specs = sorted(args, key=lambda x: x[0])

    def apply_values(self, *args: float):
        v, = args

        selected_color = self.fg_color
        if self.color_specs:
            for spec in reversed(self.color_specs):
                t, c = spec
                if t <= v:
                    selected_color = c
                    break

        for i in range(len(self.colors)):
            self.colors[i] = selected_color


class ChartSource(app.InfiniteColorSource):

    def __init__(self, pixels: Sequence[int], chart: Chart, *args: Callable[[], float]):
        super().__init__(pixels, True, chart.bg_color)
        self.chart = chart
        self.value_sources = args

    def get_colors(self, num_pixels: int) -> Dict[int, color.Color]:
        self.chart.set_values(*(s() for s in self.value_sources))
        return {i: self.chart.colors[i] for i in range(num_pixels)}


class Factory(abc.ABC):
    DEFAULT_FG_COLOR = color.NamedColor.WHITE
    DEFAULT_BG_COLOR = color.NamedColor.BLACK

    @classmethod
    def spec(cls, v_min: float = 0.0, v_max: float = 1.0, capped=False, normalised=False) -> ValueSpecification:
        if not v_min < v_max:
            raise ValueError('v_min is not less than v_max')

        return ValueSpecification(v_min, v_max, capped, normalised)

    @classmethod
    def spec_normalized(cls, spec: ValueSpecification) -> ValueSpecification:
        return cls.spec(spec.min, spec.max, spec.is_capped, True)

    @classmethod
    def bar_chart_source(cls, pixels: Sequence[int],
                         value_source: Callable[[], float],
                         spec: Optional[ValueSpecification] = None,
                         fg_color: Optional[color.Color] = None,
                         bg_color: Optional[color.Color] = None):
        return ChartSource(pixels, BarChart(len(pixels),
                                            fg_color or Factory.DEFAULT_FG_COLOR,
                                            bg_color or Factory.DEFAULT_BG_COLOR,
                                            spec or Factory.spec()),
                           value_source)

    @classmethod
    def red_blue_bar_chart_source(cls, pixels: Sequence[int],
                                  red_source: Callable[[], float],
                                  blue_source: Callable[[], float],
                                  red_spec: Optional[ValueSpecification] = None,
                                  blue_spec: Optional[ValueSpecification] = None,
                                  brightness: float = 1.0,
                                  bg_shade: float = 0.25):
        return ChartSource(pixels, RedBlueBarChart(len(pixels),
                                                   red_spec or Factory.spec(),
                                                   blue_spec or Factory.spec(),
                                                   brightness,
                                                   bg_shade),
                           red_source,
                           blue_source)

    @classmethod
    def bin_number_source(cls, pixels: Sequence[int],
                          value_source,
                          capped: bool = False,  # prefer error for out of bounds values
                          fg_color: Optional[color.Color] = None,
                          bg_color: Optional[color.Color] = None):
        return ChartSource(pixels, BinNumber(len(pixels),
                                             capped,
                                             fg_color or Factory.DEFAULT_FG_COLOR,
                                             bg_color or Factory.DEFAULT_BG_COLOR),
                           value_source)

    @classmethod
    def red_blue_bin_number_source(cls, pixels: Sequence[int],
                                   red_source: Callable[[], float],
                                   blue_source: Callable[[], float],
                                   capped: bool = False,  # prefer error for out of bounds values
                                   brightness: float = 1.0,
                                   bg_shade: float = 0.25):
        return ChartSource(pixels, RedBlueBinNumber(len(pixels),
                                                    capped,
                                                    brightness,
                                                    bg_shade),
                           red_source,
                           blue_source)

    @classmethod
    def single_stat_source(cls, pixels: Sequence[int],
                           spec: ValueSpecification,
                           default_color: color.Color,
                           *args: Tuple[float, color.Color]):
        return ChartSource(pixels, SingleStat(len(pixels), spec, default_color, *args))

    @classmethod
    def health_stat_source(cls, pixels: Sequence[int],
                           spec: ValueSpecification,
                           t_warn: float,
                           t_err: float):
        return ChartSource(pixels,
                           SingleStat(len(pixels), spec, color.NamedColor.GREEN, (t_warn, color.NamedColor.YELLOW),
                                      (t_err, color.NamedColor.RED)))
