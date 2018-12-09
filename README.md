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
application.configure_worker([animation.Rainbow(application.pixels[0:13], 60)], 0.1)
application.configure_worker([animation.LedTest(application.pixels[13:27])], 0.2)
application.exec()
```

Using charts (requires `psutil`):
```python
import psutil

from phalski_ledshim import app, chart

application = app.App()
source = chart.Factory.bar_chart_source(application.pixels, lambda: psutil.cpu_percent())
application.configure_worker([source], 0.1)
application.exec()

```
