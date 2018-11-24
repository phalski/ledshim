from __future__ import absolute_import

import abc
import queue
import threading
import logging

from typing import Sequence, List

from phalski_ledshim import color, client as ledshim_client


class ColorSource(abc.ABC):
    """Abstract base class for algorithms that update a specific range of pixels"""

    def __init__(self, pixels: Sequence[int]):
        super().__init__()
        assert pixels
        self.pixels = pixels
        self.colors = [color.Factory.color_for(0, 0, 0, 0)] * len(pixels)

    def open(self):
        pass

    @abc.abstractmethod
    def next_colors(self, previous_colors: List[color.Color]) -> List[color.Color]:
        pass

    def _update_colors(self):
        colors = self.next_colors(self.colors)
        assert len(self.pixels) == len(colors)
        self.colors = colors

    def events(self) -> List[ledshim_client.ChangeEvent]:
        self._update_colors()
        return [ledshim_client.ChangeEvent([x], self.colors[i]) for i, x in enumerate(self.pixels)]
            
    def close(self):
        pass


class Worker(threading.Thread):

    def __init__(self, name: str, streams: Sequence[ColorSource], shutdown: threading.Event, delay: float):
        super().__init__(name=name)
        assert streams
        self.log = logging.getLogger('%s.%s_%s' % (__name__, self.__class__.__name__, name))
        self.queue = queue.Queue(1)
        self.shutdown = shutdown
        self.delay = delay
        self.streams = streams

    def events(self) -> List[ledshim_client.ChangeEvent]:
        events = []
        for stream in self.streams:
            events += stream.events()

        return events

    def run(self):
        for stream in self.streams:
            stream.open()
        
        self.log.debug('Started - streams=%d,delay=%.2f' % (len(self.streams), self.delay))
        while not self.shutdown.is_set():
            if self.queue.empty():
                events = self.events()
                if events:
                    self.queue.put(events)

            self.shutdown.wait(self.delay)

        for stream in self.streams:
            stream.close()

        self.log.debug('Stopped')


class App(threading.Thread):

    def __init__(self, client: ledshim_client.Client, delay: float = 1/16):
        super().__init__()
        self.client = client
        self.delay = delay
        self.shutdown = threading.Event()
        self.workers = []
        self.log = logging.getLogger('.'.join([__name__, self.__class__.__name__]))

    @property
    def pixels(self):
        return self.client.pixels

    def configure_worker(self, streams: Sequence[ColorSource], delay: float, name=None):
        if not name:
            name = len(self.workers)
        self.workers.append(Worker(name, streams, self.shutdown, delay))

    def run(self):
        assert self.workers

        queues = [c.queue for c in self.workers]
        self.log.info('Starting %d worker(s)' % len(self.workers))
        for worker in self.workers:
            worker.start()

        self.log.info('Started - delay=%.2f' % self.delay)
        while not self.shutdown.is_set():
            show = False
            for q in queues:
                try:
                    changes = q.get_nowait()
                    show = True
                    self.client.apply_changes(changes)
                except queue.Empty:
                    # noop
                    pass

            if show:
                self.client.show()

            self.shutdown.wait(self.delay)

        self.log.info('Stopped')

    def stop_workers(self):
        self.shutdown.set()
        for worker in self.workers:
            worker.join()
