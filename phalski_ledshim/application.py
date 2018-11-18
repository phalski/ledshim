"""Application toolkit for building ledshim apps

"""

import abc
import queue
import threading
import typing

from phalski_ledshim.client import Client, ChangeEvent, ChangeEventFactory
from phalski_ledshim.color import Color, ColorDepth, ColorFactory

DEFAULT_DELAY = 1 / 16


class BaseColorChanger(abc.ABC):
    """Abstract base class for algorithm implementations

    Provides color change events that can be applied to the ledshim
    """

    @abc.abstractmethod
    def get_changes(self) -> typing.Tuple[ChangeEvent]:
        """Returns color change events for pixels

        If no changes are present, an empty tuple is returned

        To be implemented by the algorithm
        """


class ColorChanger(BaseColorChanger):
    """Abstract base class for algorithms that use a specific range of pixels"""

    def __init__(self, pixels: typing.Sequence[int]):
        super().__init__()
        if not pixels:
            raise ValueError('Pixel sequence is empty')

        self._pixels = pixels

    @abc.abstractmethod
    def _get_colors(self, n: int) -> typing.Tuple[Color]:
        """Returns the amount of requested colors

        To be implemented by subclass

        :param n: The number of colors that should be produced
        :return: The produced colors
        """

    def get_changes(self) -> typing.Tuple[ChangeEvent]:
        colors = self._get_colors(len(self._pixels))
        if colors and len(self._pixels) == len(colors):
            return tuple(ChangeEventFactory.change_for(colors[i], x) for i, x in enumerate(self._pixels))
        else:
            # TODO log error properly
            print('Illegal amount of colors: expected=%d actual=%d, no changes generated' % (
            len(self._pixels), len(colors) if colors else 0))
            return tuple()


class EventProcessor(threading.Thread):

    def __init__(self, client: Client, shutdown: threading.Event, delay: float, queues: typing.Sequence[queue.Queue]):
        super().__init__()
        self._client = client
        self._shutdown = shutdown
        self._delay = delay
        self._queues = queues

    def run(self):
        print('%s: started' % self)
        while not self._shutdown.is_set():
            show = False
            for q in self._queues:
                try:
                    changes = q.get_nowait()
                    show = True
                    self._client.apply_changes(changes)
                except queue.Empty:
                    pass

            if show:
                self._client.show()

            self._shutdown.wait(self._delay)

        print('%s: stopped' % self)


class BaseEventSource(threading.Thread, abc.ABC):

    def __init__(self, shutdown: threading.Event, delay: float):
        super().__init__()
        self._queue = queue.Queue(1)
        self._shutdown = shutdown
        self._delay = delay

    @property
    def queue(self):
        return self._queue

    @abc.abstractmethod
    def get_changes(self) -> typing.Tuple[ChangeEvent]:
        pass

    def run(self):
        print('%s: started' % self)
        while not self._shutdown.is_set():
            if self._queue.empty():
                changes = self.get_changes()
                if changes:
                    self._queue.put(changes)

            self._shutdown.wait(self._delay)

        print('%s: stopped' % self)


class ColorChangersSource(BaseEventSource):

    def __init__(self, changers: typing.Sequence[BaseColorChanger], shutdown: threading.Event, delay: float):
        super().__init__(shutdown, delay)
        self._changers = changers

    def get_changes(self):
        return (change for changer in self._changers for change in changer.get_changes())


class Application:

    def __init__(self, delay: float = DEFAULT_DELAY, brightness: float = ColorFactory.MAX_BRIGHTNESS,
                 depth: ColorDepth = ColorDepth.BIT24):
        self._client = Client(brightness, True, depth)
        self._delay = delay
        self._shutdown = None
        self._threads = []

    @property
    def pixels(self):
        return self._client.pixels

    def startup(self, *args: typing.Tuple[typing.Sequence[BaseColorChanger], float]):
        if self._shutdown is None:
            shutdown = threading.Event()
            self._threads = [ColorChangersSource(changers, shutdown, delay) for changers, delay in args]
            self._threads.append(EventProcessor(self._client, shutdown, self._delay, [p.queue for p in self._threads]))

            for t in self._threads:
                t.start()

            self._shutdown = shutdown

    def shutdown(self):
        if not self._shutdown is None:
            self._shutdown.set()
            for t in self._threads:
                t.join()
            self._shutdown = None

    def exec(self, *args: typing.Tuple[typing.Sequence[BaseColorChanger], float]):
        self.startup(*args)

        try:
            while True:
                # keep the main thread sleeping
                self._shutdown.wait(60 * 60)
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()
