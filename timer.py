from PyQt5.QtCore import QTimer
import time
import logging
from PyQt5.QtWidgets import QInputDialog

class TimerManager:
    def __init__(self, update_callback):
        self.running = False
        self.paused = False
        self.elapsed_time = 0
        self.start_time = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.update_callback = update_callback
        self.logger = logging.getLogger(__name__)

    def start(self):
        if not self.running:
            self.start_time = time.time()
            self.running = True
            self.paused = False
            self.elapsed_time = 0
            self.timer.start(1000)
            self.logger.debug("Timer started")
            return "타이머 시작됨"
        return None

    def toggle_pause(self):
        if not self.running:
            raise ValueError("타이머가 시작되지 않음")
        self.paused = not self.paused
        self.logger.debug(f"Timer {'paused' if self.paused else 'resumed'}")
        return "타이머 일시정지됨" if self.paused else "타이머 재개됨"

    def reset(self):
        if not self.running:
            raise ValueError("타이머가 시작되지 않음")
        self.elapsed_time = 0
        self.timer.stop()
        self.running = False
        self.paused = False
        self.start_time = None
        self.update_callback(0, 0)
        self.logger.debug("Timer reset")
        return "타이머 초기화됨"

    def update(self):
        if not self.paused:
            self.elapsed_time += 1
            minutes = self.elapsed_time // 60
            seconds = self.elapsed_time % 60
            self.update_callback(minutes, seconds)
            self.logger.debug(f"Timer updated: {self.elapsed_time} seconds")

    def edit_time(self, parent):
        if not self.running:
            raise ValueError("타이머가 시작되지 않음")
        new_time, ok = QInputDialog.getText(parent, '타이머 시간 수정', '새 시간을 입력하세요 (MM:SS 형식):')
        if ok and new_time:
            try:
                minutes, seconds = map(int, new_time.split(':'))
                self.elapsed_time = minutes * 60 + seconds
                self.update_callback(minutes, seconds)
                self.logger.debug(f"Timer time edited to {minutes:02}:{seconds:02}")
                return "시간 수정됨"
            except ValueError:
                self.logger.warning("Invalid time format in edit_time")
                raise ValueError("올바른 형식(MM:SS)으로 입력하세요.")
        return None

    def get_elapsed_time(self):
        return self.elapsed_time