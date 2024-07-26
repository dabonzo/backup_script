from datetime import datetime


class Logger:
    def __init__(self, log_file, verbose=False):
        self.log_file = log_file
        self.verbose = verbose

    def log(self, message, section=False):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if section:
            section_length = max(30, len(message) + 4)  # Ensure a minimum length for the section headers
            header = f"\n{'#' * section_length}\n# {message.center(section_length - 4)} #\n{'#' * section_length}\n"
            formatted_message = f"{timestamp} - {header}"
        else:
            formatted_message = f"{timestamp} - {message}"

        with open(self.log_file, "a") as log_file:
            log_file.write(formatted_message + "\n")
        if self.verbose:
            print(formatted_message)
