# logger.py
from datetime import datetime
import inspect

class Logger:
    """
    A singleton logger class to handle logging messages to a file and printing to the console.
    """
    _instance = None

    @staticmethod
    def get_instance(log_file=None, verbose=False, debug=False):
        """
        Static access method to get the singleton instance of the Logger.
        :param log_file: Path to the log file.
        :param verbose: Whether to print log messages to stdout.
        :param debug: Whether to print debug messages.
        :return: Singleton instance of Logger.
        """
        if Logger._instance is None:
            if log_file is None:
                raise ValueError("Logger has not been initialized. Provide log_file, verbose, and debug parameters.")
            Logger(log_file, verbose, debug)
        return Logger._instance

    def __init__(self, log_file, verbose=False, debug=False):
        """
        Virtually private constructor.
        :param log_file: Path to the log file.
        :param verbose: Whether to print log messages to stdout.
        :param debug: Whether to print debug messages.
        """
        if Logger._instance is not None:
            raise Exception("This class is a singleton!")
        else:
            Logger._instance = self

        self.log_file = log_file
        self.verbose = verbose
        self.debug = debug

    def log(self, message, section=False):
        """
        Log a message.
        :param message: Message to log.
        :param section: Whether to format the message as a section header.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"{timestamp} - {message}" if not section else f"\n{'#' * 22}\n# {message.center(18)} #\n{'#' * 22}\n"
        with open(self.log_file, "a") as log_file:
            log_file.write(formatted_message + "\n")
        if self.verbose:
            print(formatted_message)

    def debug_log(self, message):
        """
        Log a debug message if debugging is enabled.
        :param message: Debug message to log.
        """
        if self.debug:
            frame = inspect.currentframe().f_back
            filename = inspect.getframeinfo(frame).filename
            lineno = frame.f_lineno
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_message = f"{timestamp} - DEBUG: {filename}:{lineno} - {message}"
            print(formatted_message)
            with open(self.log_file, "a") as log_file:
                log_file.write(formatted_message + "\n")
