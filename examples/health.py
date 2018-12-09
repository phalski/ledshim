import time
import math

from phalski_ledshim import app, chart


def value():
    t = time.time()
    return (math.sin(t) + 1) / 2


if __name__ == '__main__':
    a = app.App()
    a.configure_worker(0.1, chart.Factory.health_stat_source(a.pixels, value, chart.Factory.spec(0, 1, True), 0.5, 0.7))
    a.exec()
