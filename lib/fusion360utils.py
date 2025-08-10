import adsk.core
import adsk.fusion
import traceback

app = adsk.core.Application.get()
ui = app.userInterface


def log(message: str):
    """Log message to Text Commands window"""
    app.log(message)


def handle_error(context: str):
    """Handle and log errors"""
    ui.messageBox(f'Error in {context}:\n{traceback.format_exc()}')


def clear_handlers():
    """Clear all event handlers"""
    handlers = []
    for handler in handlers:
        handler.remove()
    handlers.clear()


def add_handler(event, handler_function, local_handlers=None):
    """Add an event handler"""
    handler = event.add(handler_function)
    if local_handlers:
        local_handlers.append(handler)
    return handler
