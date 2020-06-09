from datetime import datetime


class Logger():
    def __init__(self):
        pass

    def log(self, message):
        time = datetime.now().strftime("%H:%M:%S")
        print(f'[{time}] {message}')
