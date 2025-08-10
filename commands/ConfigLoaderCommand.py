"""Placeholder command for configuration loading."""

import adsk.core
import adsk.fusion
from ..lib import fusion360utils as futil
from .. import config

app = adsk.core.Application.get()
ui = app.userInterface

CMD_NAME = 'Config Loader'
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_configLoader'
CMD_Description = 'Load configuration settings'


def start():
    # Placeholder for potential future implementation
    pass


def stop():
    pass
