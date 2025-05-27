
import structlog
import logging
from rich.console import Console
from rich.traceback import install as rich_traceback_install
from structlog.processors import CallsiteParameter

#better_exceptions.MAX_LENGTH = None
rich_traceback_install(show_locals=False, width=180, 
                       extra_lines=3, theme="lightbulb", word_wrap=True)

def reorder_keys(logger, method_name, event_dict):
    """Custom processor to reorder log keys."""
    log_key_order = [
        'timestamp', 'level', #'event', 'logger',
        'conversation_id', 
        
        'from_', 'from_contact', 'to', 'to_contact', 'status',
        'duration', 
        'type', 'message_type', 'body', 'message', 
        'id', 'request_id', 'twilio_request_id',
        'filename', 'module', 'lineno', 'func_name','_sa_instance_state'
    ]
    ordered_dict = {}
    
    # Add keys in desired order if they exist
    for key in log_key_order:
        if key in event_dict:
            ordered_dict[key] = event_dict[key]
    
    # Add any remaining keys that weren't in the desired order
    for key, value in event_dict.items():
        if key not in ordered_dict:
            ordered_dict[key] = value
    
    return ordered_dict

# Configure structlog to use colorized output for the terminal
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.CallsiteParameterAdder(parameters={CallsiteParameter.FILENAME, CallsiteParameter.FUNC_NAME, CallsiteParameter.LINENO, CallsiteParameter.MODULE}, additional_ignores=None),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
        structlog.processors.StackInfoRenderer(),
        reorder_keys,
        structlog.dev.ConsoleRenderer(colors=True, 
                                      exception_formatter=structlog.dev.RichTracebackFormatter(), #structlog.dev.RichTracebackFormatter, 
                                      sort_keys=False, 
                                    ),

    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    cache_logger_on_first_use=True,
)

# Disable colorized output for the text logs
logging.basicConfig(level=logging.INFO, format="%(message)s")

logger = structlog.get_logger()


if __name__=="__main__":
    logger.info("Logging configured successfully.")