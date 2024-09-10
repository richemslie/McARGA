import os
import datetime


class Logger:
    VERBOSE = True
    DO_LOGGING = False

    def __init__(self):
        if self.DO_LOGGING:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            log_dir = os.path.join(module_dir, 'logs')
            os.makedirs(log_dir, exist_ok=True)
            self.log_file = f"{log_dir}/{self.task_id}.log"
        else:
            self.log_file = None

    def log(self, message, *args, **kwds):
        current_time = datetime.datetime.now().strftime('%H:%M:%S')
        log_message = f"[{current_time}] {message}"

        # Format the message with any additional arguments
        if args or kwds:
            log_message = log_message.format(*args, **kwds)

        if self.log_file:
            # Append the message to the log file
            with open(self.log_file, 'a') as file:
                file.write(log_message + '\n')
        else:
            if self.VERBOSE:
                print(log_message)


logger = Logger()
log = logger.log
