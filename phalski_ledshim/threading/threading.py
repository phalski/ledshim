import logging
import time

from abc import ABC, abstractmethod
from threading import Event, Thread
from typing import List, Sequence, Tuple
from queue import Queue, Empty

from .. import ColorChangeEvent, ColorSource, LedShim, Palette

__name__ = 'phalski_ledshim.threading'

FPS_DEFAULT = 1 / 16  # 16 FPS
REFRESH_DEFAULT = 0.1  # 50ms


class Consumer(Thread):

    def __init__(self, ledshim: LedShim, poison_pill: Event, refresh_interval: float = FPS_DEFAULT, *args: Queue):
        super().__init__()
        self._ledshim = ledshim
        self._poison_pill = poison_pill
        self._refresh_interval = refresh_interval
        self._queues = args

    def run(self):
        print('%s: started' % self)
        while not self._poison_pill.is_set():
            show = False
            for q in self._queues:
                try:
                    events = q.get_nowait()
                    show = True
                    self._ledshim.apply(events)
                except Empty:
                    pass

            if show:
                self._ledshim.show()

            self._poison_pill.wait(self._refresh_interval)

        print('%s: stopped' % self)


class Producer(Thread, ABC):

    def __init__(self, poison_pill: Event, refresh_interval: float = REFRESH_DEFAULT):
        super().__init__()
        self._queue = Queue(1)
        self._poison_pill = poison_pill
        self._refresh_interval = refresh_interval

    @property
    def queue(self):
        return self._queue

    @abstractmethod
    def produce(self) -> List[ColorChangeEvent]:
        pass

    def run(self):
        print('%s: started' % self)
        while not self._poison_pill.is_set():
            if self._queue.empty():
                product = self.produce()
                if product:
                    self._queue.put(product)

            self._poison_pill.wait(self._refresh_interval)

        print('%s: stopped' % self)


class ColorSourceProducer(Producer):

    def __init__(self, source: ColorSource, poison_pill: Event, refresh_interval: float = REFRESH_DEFAULT):
        super().__init__(poison_pill, refresh_interval)
        self._source = source

    def produce(self):
        return self._source.get()


class ExampleProducer(Producer):

    def __init__(self, pixels: Sequence[int], poison_pill: Event, refresh_interval: float = REFRESH_DEFAULT):
        super().__init__(poison_pill, refresh_interval)
        self._pixels = pixels
        self._counter = 0
        self._colors = Palette.colors()

    def produce(self):
        i_p = self._counter % len(self._pixels)
        i_c = self._counter % len(self._colors)
        e = [ColorChangeEvent([self._pixels[i_p]], self._colors[i_c])]
        self._counter += 1
        return e


class Application:

    def __init__(self, refresh_interval: float = FPS_DEFAULT, brightness: float = 1.0, clear_on_exit: bool = True):
        self._logger = logging.getLogger('%s.%s' % (__name__, self.__class__.__name__))
        self._logger.setLevel(logging.DEBUG)
        print(self._logger)
        self._logger.warning('%s.%s' % (__name__, self.__class__.__name__))

        self._ledshim = LedShim(brightness, clear_on_exit)
        self._refresh_interval = refresh_interval
        self._poison_pill = Event()
        self._threads = []

    @property
    def pixels(self):
        return self._ledshim.pixels

    def startup(self, *args: Tuple[ColorSource, float]):
        self._threads = [ColorSourceProducer(source, self._poison_pill, refresh_interval) for source, refresh_interval
                         in args]
        self._threads.append(
            Consumer(self._ledshim, self._poison_pill, self._refresh_interval, *(p.queue for p in self._threads)))

        for t in self._threads:
            t.start()

    def shutdown(self):
        self._poison_pill.set()
        for t in self._threads:
            t.join()

    def exec(self, *args: Tuple[ColorSource, float]):
        self.startup(*args)

        try:
            while True:
                time.sleep(60 * 60)
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()
