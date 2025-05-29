import time
from typing import Callable, Dict
from PyQt5.QtWidgets import QInputDialog, QWidget
import logging

class TimerManager:
    def __init__(self, update_callback: Callable[[int, int, int], None]):
        self.logger = logging.getLogger(__name__)
        self.elapsed_time = 0
        self.start_time = None
        self.paused = False
        self.running = False
        self.update_callback = update_callback
        self.last_update = 0

    def start(self) -> str:
        try:
            if self.running:
                raise ValueError("타이머가 이미 실행 중입니다.")
            self.running = True
            self.paused = False
            self.start_time = time.time() - self.elapsed_time
            self._update()
            return "타이머 시작"
        except Exception as e:
            self.logger.error(f"Error starting timer: {str(e)}")
            raise

    def toggle_pause(self) -> str:
        try:
            if not self.running:
                raise ValueError("타이머가 실행 중이 아닙니다.")
            if self.paused:
                self.paused = False
                self.start_time = time.time() - self.elapsed_time
                self._update()
                return "타이머 재개"
            else:
                self.paused = True
                return "타이머 일시정지"
        except Exception as e:
            self.logger.error(f"Error toggling pause: {str(e)}")
            raise

    def reset(self) -> str:
        try:
            self.elapsed_time = 0
            self.start_time = None
            self.paused = False
            self.running = False
            self.update_callback(0, 0, 0)
            return "타이머 초기화"
        except Exception as e:
            self.logger.error(f"Error resetting timer: {str(e)}")
            raise

    def get_elapsed_time(self) -> int:
        try:
            if self.running and not self.paused:
                self.elapsed_time = int(time.time() - self.start_time)
            return self.elapsed_time
        except Exception as e:
            self.logger.error(f"Error getting elapsed time: {str(e)}")
            raise

    def _update(self):
        try:
            if self.running and not self.paused:
                current_time = time.time()
                self.elapsed_time = int(current_time - self.start_time)
                minutes = self.elapsed_time // 60
                seconds = self.elapsed_time % 60
                if int(current_time) > self.last_update:
                    self.last_update = int(current_time)
                    self.update_callback(minutes, seconds, self.elapsed_time)
                from threading import Timer
                timer = Timer(0.1, self._update)
                timer.daemon = True
                timer.start()
        except Exception as e:
            self.logger.error(f"Error updating timer: {str(e)}")

    def edit_time(self, parent: QWidget, error_handler: Callable[[str], None]) -> tuple:
        try:
            time_str, ok = QInputDialog.getText(parent, "타이머 시간 수정", "새 시간을 입력하세요 (MM:SS):")
            if not ok:
                return None, "시간 수정 취소"
            try:
                minutes, seconds = map(int, time_str.split(':'))
                new_time = minutes * 60 + seconds
                if new_time < 0:
                    raise ValueError("음수 시간은 허용되지 않습니다.")
                from commands import EditTimeCommand
                command = EditTimeCommand(self, self.elapsed_time, new_time)
                return command, "시간 수정됨"
            except ValueError as e:
                error_handler(f"잘못된 시간 형식입니다: {str(e)}")
                return None, ""
        except Exception as e:
            self.logger.error(f"Error editing time: {str(e)}")
            raise

    def set_time(self, new_time: int):
        try:
            self.elapsed_time = new_time
            if self.running and not self.paused:
                self.start_time = time.time() - self.elapsed_time
            minutes = self.elapsed_time // 60
            seconds = self.elapsed_time % 60
            self.update_callback(minutes, seconds, self.elapsed_time)
        except Exception as e:
            self.logger.error(f"Error setting time: {str(e)}")
            raise

    def get_state(self) -> Dict:
        try:
            return {
                'elapsed_time': self.elapsed_time,
                'running': self.running,
                'paused': self.paused
            }
        except Exception as e:
            self.logger.error(f"Error getting state: {str(e)}")
            raise

    def restore_state(self, state: Dict):
        try:
            self.elapsed_time = state.get('elapsed_time', 0)
            self.running = state.get('running', False)
            self.paused = state.get('paused', False)
            if self.running and not self.paused:
                self.start_time = time.time() - self.elapsed_time
                self._update()  # 실행 중이면 업데이트 시작
            else:
                self.start_time = None
            minutes = self.elapsed_time // 60
            seconds = self.elapsed_time % 60
            self.update_callback(minutes, seconds, self.elapsed_time)
            self.logger.debug("Timer state restored: running=%s, paused=%s, elapsed=%d", self.running, self.paused, self.elapsed_time)
        except Exception as e:
            self.logger.error(f"Error restoring state: {str(e)}")
            raise