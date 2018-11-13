"""Application toolkit for building ledshim apps

"""

import abc
import typing

import phalski_ledshim.client as client
import phalski_ledshim.color as color


class ColorChanger(abc.ABC):
    """Abstract base class for algorithm implementations

    A ColorChanger instance is initialized for specific pixels and provides color change events for those pixels only.
    """

    def __init__(self, pixels: typing.Sequence[int]):
        super().__init__()
        if not pixels:
            raise ValueError('Pixel sequence is empty')

        self._pixels = pixels

    def _changes_for(self, colors: typing.Sequence[color.Color]) -> typing.Tuple[client.ChangeEvent]:
        """Helper function to produce change events for all pixels

        The given color sequence is mapped to the internal pixel sequence by index. This only works if both sequences
        have the same length.

        :param colors: A sequence of colors
        :raises ValueError: If the color sequence is not of the exact same length than the pixel sequence length of this
        changer instance.
        :return: Change events for the given colors
        """
        if not colors or not len(self._pixels) == len(colors):
            # this helper requires a new color for every pixels otherwise the mapping does not work
            raise ValueError(
                'Illegal amount of colors: expected=%d actual=%d' % (len(self._pixels), len(colors) if colors else 0))

        return tuple(client.change_for(colors[i], x) for i, x in enumerate(self._pixels))

    @abc.abstractmethod
    def get_changes(self) -> typing.Optional[typing.Tuple[client.ChangeEvent]]:
        """Returns color change events for pixels

        If no changes are present, None is returned

        To be implemented by the algorithm
        """
