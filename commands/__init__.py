# Define the command definitions
from . import BinGeneratorCommand
from . import BatchProcessorCommand
from . import ConfigLoaderCommand

# List of commands
commands = [
    BinGeneratorCommand,
    BatchProcessorCommand,
    ConfigLoaderCommand
]

# Initialize the commands
def start():
    for command in commands:
        command.start()

def stop():
    for command in commands:
        command.stop()
