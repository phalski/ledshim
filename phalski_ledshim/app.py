from __future__ import absolute_import

import abc
import queue
import threading
import logging

from typing import Generator, Optional, Sequence, List, Dict

from phalski_ledshim import color, client as ledshim_client


class SourceError(Exception):
    pass


class BaseColorSource(abc.ABC):

    def __init__(self):
        super().__init__()

    def open(self):
        pass

    @abc.abstractmethod
    def events(self) -> Generator[List[ledshim_client.ChangeEvent], None, None]:
        pass

    def close(self):
        """Closes all resources used by the source (e.g. file handles, db connections, ...)"""
        pass


class MultiSource(BaseColorSource):

    def __init__(self, *args: BaseColorSource):
        super().__init__()
        self.sources = list(args)

    def events(self) -> Generator[List[ledshim_client.ChangeEvent], None, None]:
        event_generators = [source.events() for source in self.sources]

        while event_generators:
            events = []
            for i, generator in enumerate(event_generators):
                try:
                    events += next(generator)
                except StopIteration:
                    event_generators.remove(generator)
                    self.sources.pop(i).close()

            yield events

    def close(self):
        for source in self.sources:
            source.close()


class ColorSource(BaseColorSource):
    """Abstract base class for algorithms that update a specific range of pixels"""

    def __init__(self, pixels: Sequence[int], clear: bool = False,
                 clear_color: color.Color = color.Factory.color(0, 0, 0)):
        super().__init__()
        assert pixels
        self.pixels = pixels
        self.clear_color = clear_color
        self.clear = clear
        self.color_values = [clear_color] * len(pixels)

    @abc.abstractmethod
    def colors(self, num_pixels: int) -> Generator[Dict[int, color.Color], None, None]:
        pass

    def events(self) -> Generator[List[ledshim_client.ChangeEvent], None, None]:
        colors_generator = self.colors(len(self.pixels))
        while True:
            try:
                colors = next(colors_generator)
                events = []
                for i, x in enumerate(self.pixels):
                    if i in colors:
                        self.color_values[i] = colors[i]
                    elif self.clear:
                        self.color_values[i] = self.clear_color

                    events.append(ledshim_client.Factory.change_event(self.color_values[i], x))
                yield events
            except StopIteration:
                if self.clear:
                    yield [ledshim_client.Factory.change_event(self.clear_color, x) for x in self.pixels]
                break


class InfiniteColorSource(ColorSource):

    def __init__(self, pixels: Sequence[int], clear: bool = False,
                 clear_color: color.Color = color.Factory.color(0, 0, 0)):
        super().__init__(pixels, clear, clear_color)

    def colors(self, num_pixels: int) -> Generator[Dict[int, color.Color], None, None]:
        while True:
            yield self.get_colors(num_pixels)

    @abc.abstractmethod
    def get_colors(self, num_pixels: int) -> Dict[int, color.Color]:
        pass


class Worker(threading.Thread):

    def __init__(self, name: str, source: BaseColorSource, shutdown: threading.Event, delay: float):
        super().__init__(name=name)
        self.log = logging.getLogger('%s.%s_%s' % (__name__, self.__class__.__name__, self.name))
        self.queue = queue.Queue(1)
        self.shutdown = shutdown
        self.delay = delay
        self.source = source

    def run(self):
        try:
            self.source.open()
        except SourceError:
            self.log.exception('Failed to open source')

        events = self.source.events()

        self.log.info('Consuming from source with a delay of %.2fs' % self.delay)
        while not self.shutdown.is_set():
            if self.queue.empty():
                try:
                    self.queue.put(next(events))
                except SourceError:
                    self.log.exception('Failed to get events from source')
                    break
                except StopIteration:
                    break

            self.shutdown.wait(self.delay)

        self.source.close()

        if self.shutdown.is_set():
            self.log.info('Stopped')
        else:
            self.log.info('Finished')


class App(threading.Thread):

    def __init__(self, delay: float = 1 / 16, client: Optional[ledshim_client.Client] = None):
        super().__init__()
        self.client = client or ledshim_client.Factory.client()
        self.delay = delay
        self.shutdown = threading.Event()
        self.workers = []
        self.log = logging.getLogger('.'.join([__name__, self.__class__.__name__]))

    @property
    def pixels(self):
        return self.client.pixels

    def configure_worker(self, delay: float, *args: BaseColorSource):
        self.workers.append(Worker('<%d>' % len(self.workers), MultiSource(*args), self.shutdown, delay))

    def run(self):

        self.log.info('Starting %d worker(s)' % len(self.workers))
        for worker in self.workers:
            worker.start()

        self.log.info('Started - delay=%.2f' % self.delay)
        while self.workers and not self.shutdown.is_set():
            show = False
            for worker in self.workers:
                try:
                    changes = worker.queue.get_nowait()
                    show = True
                    self.client.apply_changes(changes)
                except queue.Empty:
                    pass

                if not worker.is_alive():
                    self.workers.remove(worker)
                    self.log.info(
                        'Worker_%s finished, there are %d active workers remaining' % (worker.name, len(self.workers)))

            if show:
                self.client.show()

            self.shutdown.wait(self.delay)

        if self.shutdown.is_set():
            self.log.info('Stopped')
        else:
            self.log.info('Finished')

    def stop_workers(self):
        self.shutdown.set()
        for worker in self.workers:
            worker.join()

    def exec(self):
        self.start()
        try:
            self.join()
        except (KeyboardInterrupt, SystemExit):
            self.stop_workers()
            self.join()
