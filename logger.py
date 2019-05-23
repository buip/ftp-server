import datetime

class Logger:

    def __init__(self, filename):
        self.filename = filename

    def write_to_log_file(self, msg):
        curr_time = datetime.datetime.now()
        f = open(self.filename, "a")
        print(msg)
        f.write(f"{curr_time} {msg}")



