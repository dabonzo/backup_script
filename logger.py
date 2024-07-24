from datetime import datetime


class Logger:
    def __init__(self, log_file, verbose=False):
        self.log_file = log_file
        self.verbose = verbose

    def log(self, message, section=False):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"{timestamp} - {message}" if not section else f"\n{'#' * 22}\n# {message.center(18)} #\n{'#' * 22}\n"
        with open(self.log_file, "a") as log_file:
            log_file.write(formatted_message + "\n")
        if self.verbose:
            print(formatted_message)
