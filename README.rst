===============
phalski-ledshim
===============

A basic application framework for the Pimoroni LED SHIM.

Features:

* Easy animation development

* Flexible pixel segmenting

* Running multiple animations simultaneously

* Basic charting supported out of the box


Examples
========

Basic usage::

    from phalski_ledshim.threading import Application
    from phalski_ledshim.animation import Rainbow

    # create application with default settings: ~16fps refresh rate + full brightness
    app = Application()

    # init a rainbow animation for the first 8 using 16 colors at normal speed
    r1 = Rainbow(app.pixels[0:8])
    # init a second reverse rainbow animation on the other pixels with more colors and a faster speed
    r2 = Rainbow(list(reversed(app.pixels[8:27])), 32, 4)

    # execute both animations with a refresh_rate of 0.1 (~10 times/s)
    app.exec((r1, 0.01), (r2, 0.01))


Using charts (requires ``psutil``)::

    import psutil

    from phalski_ledshim import Color
    from phalski_ledshim.threading import Application
    from phalski_ledshim.charting import ChartSource, BarChart, ValueSpecification

    # create application with default settings: ~16fps refresh rate + full brightness
    app = Application()

    fg = Color(255, 0, 0, 1.0)  # full red
    bg = fg.dim(-0.75)  # 75% reduced foreground color

    # init a bar chart animation that accepts values between 0 and 100 and uses the above colors
    chart = BarChart(len(app.pixels), ValueSpecification(0, 100, False, True), fg, bg)

    # create a chart source that visualises the current cpu load
    source = ChartSource(app.pixels, chart, lambda: psutil.cpu_percent())

    # execute the chart source with a refresh_rate of 100ms (~10 times/s)
    app.exec((source, 0.1))

