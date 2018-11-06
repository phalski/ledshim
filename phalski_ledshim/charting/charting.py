from typing import Tuple

from .. import Color, Palette


class ValueSpecification:

    def __init__(self, v_min: float = 0.0, v_max: float = 1.0, capped=False, normalised=False):
        if not v_min < v_max:
            raise ValueError('v_min is not less than v_max')

        self._min = v_min
        self._max = v_max
        self._is_capped = capped
        self._is_normalised = normalised

    @property
    def min(self):
        return self._min

    @property
    def max(self):
        return self._max

    @property
    def is_capped(self):
        return self._is_capped

    @property
    def is_normalised(self):
        return self._is_normalised


class Chart:
    DEFAULT_COLOR = Palette.BLACK.adjust_brightness(0)

    def __init__(self, length: int, fg_color: Color, bg_color: Color, *args: ValueSpecification):
        self._colors = [Chart.DEFAULT_COLOR] * length
        self._fg_color = fg_color
        self._bg_color = bg_color
        self._value_specs = args

    @property
    def colors(self):
        return tuple(self._colors)

    @property
    def fg_color(self):
        return self._fg_color

    @property
    def bg_color(self):
        return self._bg_color

    def validate_and_process_values(self, *args: float):
        num_specs = len(self._value_specs)
        num_values = len(args)
        if not num_specs == num_values:
            raise ValueError('Illegal number of values: expected=%d actual=%d' % (num_specs, num_values))

        value_list = list(args)
        for i, spec in enumerate(self._value_specs):
            if value_list[i] < spec.min:
                if spec.is_capped:
                    value_list[i] = spec.min
                else:
                    raise ValueError('value %d=%f is lower than specified min %f' % (i, value_list[i], spec.min))
            elif spec.max < value_list[i]:
                if spec.is_capped:
                    value_list[i] = spec.max
                else:
                    raise ValueError('value at %d=%f is greater than specified max %f' % (i, value_list[i], spec.max))

            if spec.is_normalised:
                value_list[i] = (value_list[i] - spec.min) / (spec.max - spec.min)

        return tuple(value_list)

    def set_values(self, *args: float):
        raise NotImplementedError('set value must be implemented in subclass')


class BarChart(Chart):

    def __init__(self, length: int,
                 spec: ValueSpecification,
                 fg_color: Color,
                 bg_color: Color = Chart.DEFAULT_COLOR):
        super().__init__(length, fg_color, bg_color, spec)

    def set_values(self, *args: float):
        v, = self.validate_and_process_values(*args)
        v *= len(self._colors)

        for i in range(len(self._colors)):
            self._colors[i] = self.bg_color if v <= 0 else self.fg_color.shade((1 - min(v, 1.0)) * -1)
            v -= 1


class RedBlueBarChart(Chart):

    def __init__(self,
                 length: int,
                 red: ValueSpecification,
                 blue: ValueSpecification,
                 brightness: float = 1.0,
                 bg_shade: float = -0.75):
        c = Color(255, 0, 255, brightness)
        super().__init__(length, c, c.shade(bg_shade), red, blue)

    def set_values(self, *args: float):
        red, blue = (len(self._colors) * v for v in self.validate_and_process_values(*args))

        for i in range(len(self._colors)):
            r = self.bg_color.r if red <= 0 else max(self.bg_color.r,
                                                     Color.shade_saturation(self.fg_color.r, (1 - min(red, 1.0)) * -1))
            b = self.bg_color.b if blue <= 0 else max(self.bg_color.b,
                                                      Color.shade_saturation(self.fg_color.b,
                                                                             (1 - min(blue, 1.0)) * -1))
            self._colors[i] = Color(r, 0, b, self.fg_color.brightness)

            red -= 1
            blue -= 1


class BinNumber(Chart):

    def __init__(self, length: int,
                 fg_color: Color,
                 bg_color: Color = Chart.DEFAULT_COLOR):
        super().__init__(length, fg_color, bg_color, ValueSpecification(0.0, (1 << length) - 1, True))

    def set_values(self, *args: float):
        v, = self.validate_and_process_values(*args)
        n = int(v)

        for i in range(len(self._colors)):
            self._colors[i] = self.fg_color if 0 < 1 << i & n else self.bg_color


class RedBlueBinNumber(Chart):

    def __init__(self,
                 length: int,
                 brightness: float = 1.0,
                 bg_shade: float = -0.75):
        c = Palette.BLACK.adjust_brightness(brightness)
        s = ValueSpecification(0.0, (1 << length) - 1, True)
        super().__init__(length, c, c.shade(bg_shade), s, s)

    def set_values(self, *args: float):
        red, blue = (int(v) for v in self.validate_and_process_values(*args))

        for i in range(len(self._colors)):
            r = self.fg_color.r if 0 < 1 << i & red else self.bg_color.r
            b = self.fg_color.b if 0 < 1 << i & blue else self.bg_color.b
            self._colors[i] = Color(r, 0, b, self.fg_color.brightness)


class SingleStat(Chart):

    def __init__(self,
                 length: int,
                 spec: ValueSpecification,
                 default_color: Color,
                 *args: Tuple[float, Color]):
        super().__init__(length, default_color, Chart.DEFAULT_COLOR, spec)
        self._color_specs = sorted(args, key=lambda x: x[0])

    def set_values(self, *args: float):
        v, = self.validate_and_process_values(*args)

        color = self.fg_color
        if self._color_specs:
            for spec in reversed(self._color_specs):
                t, c = spec
                if t <= v:
                    color = c
                    break

        for i in range(len(self._colors)):
            self._colors[i] = color


class HealthStat(SingleStat):

    def __init__(self, length: int, spec: ValueSpecification, t_warn: float, t_err: float):
        super().__init__(length, spec, Palette.GREEN, (t_warn, Palette.YELLOW), (t_err, Palette.RED))
