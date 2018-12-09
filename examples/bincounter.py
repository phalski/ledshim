import math
import time

from phalski_ledshim import app, client, chart

class Counter(object):

    def __init__(self):
        self.count = 0

    def get_and_increment(self):
        c = self.count
        self.count += 1
        return c


if __name__ == '__main__':
    counter = Counter()
    a = app.App()
    a.configure_worker(0.001, chart.Factory.bin_number_source(a.pixels, counter.get_and_increment))
    a.exec()
