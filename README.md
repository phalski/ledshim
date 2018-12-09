# phalski-ledshim

A basic application framework for the Pimoroni LED SHIM.

Features:

* Easy animation development
* Flexible pixel segmenting
* Running multiple animations simultaneously
* Basic charting supported out of the box


## Examples

Basic usage:
```python
from phalski_ledshim import app, animation

application = app.App()
application.configure_worker(0.1, animation.Rainbow(application.pixels[0:13], 60))
application.configure_worker(0.2, animation.LedTest(application.pixels[13:27]))
application.exec()
```

Running multiple sources in a single worker:
```python
from phalski_ledshim import app, animation

application = app.App()
application.configure_worker(0.1, animation.Rainbow(application.pixels[0:13], 60), animation.LedTest(application.pixels[13:27]))
application.exec()
```

Using charts (requires `psutil`):
```python
import psutil

from phalski_ledshim import app, chart

application = app.App()
source = chart.Factory.bar_chart_source(application.pixels, lambda: psutil.cpu_percent())
application.configure_worker(0.1, source)
application.exec()

```
