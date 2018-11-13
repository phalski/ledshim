import logging

from phalski_ledshim.threading import Application
from phalski_ledshim.animation import Rainbow

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)
logger.info('hello')

# create application with default settings: ~16fps refresh rate + full brightness
app = Application()

# init a rainbow animation for the first 8 using 16 colors at normal speed
r1 = Rainbow(app.pixels[0:8])
# init a second reverse rainbow animation on the other pixels with more colors and a faster speed
r2 = Rainbow(list(reversed(app.pixels[8:27])), 32, 4)

# execute both animations with a refresh_rate of 0.1 (~10 times/s)
app.exec((r1, 0.01), (r2, 0.01))