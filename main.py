import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from ui import HighlightRecorderUI
from timer import TimerManager
from highlight import HighlightManager
from save import SaveManager

# 로깅 설정
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class HighlightRecorderApp:
    def __init__(self):
        try:
            self.logger = logging.getLogger(__name__)
            self.logger.debug("HighlightRecorderApp initializing")
            self.app = QApplication(sys.argv)
            self.timer_manager = TimerManager(self.update_timer_callback)
            self.highlight_manager = HighlightManager()
            self.save_manager = SaveManager(None)
            callbacks = {
                'start_match': self.start_match,
                'toggle_timer': self.toggle_timer,
                'reset_timer': self.reset_timer,
                'record_highlight': self.record_highlight,
                'edit_match_time': self.edit_match_time,
                'delete_highlight': self.delete_highlight,
                'edit_highlight': self.edit_highlight_inline,
                'save_highlights': self.save_highlights,
            }
            self.ui = HighlightRecorderUI(callbacks)
            self.save_manager.parent = self.ui
            self.ui.closeEvent = self.close_event
            self.logger.debug("HighlightRecorderApp initialized successfully")
        except Exception as e:
            print(f"Error initializing HighlightRecorderApp: {str(e)}")
            raise

    def update_timer_callback(self, minutes, seconds):
        self.ui.update_timer_display(minutes, seconds)

    def start_match(self):
        try:
            message = self.timer_manager.start()
            if message:
                self.ui.update_status(message)
        except Exception as e:
            self.logger.error(f"Error in start_match: {str(e)}")
            self.ui.show_error(f"타이머 시작 중 오류: {str(e)}")

    def toggle_timer(self):
        try:
            message = self.timer_manager.toggle_pause()
            self.ui.update_status(message)
            self.ui.pause_button.setText('타이머 재개' if self.timer_manager.paused else '타이머 일시정지')
        except ValueError as e:
            self.logger.warning(str(e))
            self.ui.show_warning("오류", str(e))
        except Exception as e:
            self.logger.error(f"Error in toggle_timer: {str(e)}")
            self.ui.show_error(f"타이머 토글 중 오류: {str(e)}")

    def reset_timer(self):
        try:
            message = self.timer_manager.reset()
            self.ui.update_status(message)
            self.ui.record_button.setText('하이라이트 기록')
            self.highlight_manager.highlight_start_time = None
        except ValueError as e:
            self.logger.warning(str(e))
            self.ui.show_warning("오류", str(e))
        except Exception as e:
            self.logger.error(f"Error in reset_timer: {str(e)}")
            self.ui.show_error(f"타이머 초기화 중 오류: {str(e)}")

    def record_highlight(self):
        try:
            current_time = self.timer_manager.get_elapsed_time()
            if self.highlight_manager.highlight_start_time is None:
                message = self.highlight_manager.start_recording(current_time)
                if message:
                    self.ui.update_status(message)
                    self.ui.record_button.setText('기록 중지')
                    self.ui.memo_input.setFocus()
            else:
                memo = self.ui.get_memo()
                message = self.highlight_manager.stop_recording(current_time, memo)
                if message:
                    self.ui.update_status(message)
                    self.ui.record_button.setText('하이라이트 기록')
                    self.ui.clear_memo()
                    self.ui.update_highlights_view(self.highlight_manager.get_highlights())
                    self.save_manager.saved = False
        except ValueError as e:
            self.logger.warning(str(e))
            self.ui.show_warning("오류", str(e))
        except Exception as e:
            self.logger.error(f"Error in record_highlight: {str(e)}")
            self.ui.show_error(f"하이라이트 기록 중 오류: {str(e)}")

    def delete_highlight(self):
        try:
            index = self.ui.get_selected_highlight_index()
            if index == -1:
                self.ui.show_info("알림", "삭제할 하이라이트를 선택하세요.")
                return
            message = self.highlight_manager.delete(index)
            self.ui.update_status(message)
            self.ui.update_highlights_view(self.highlight_manager.get_highlights())
            self.save_manager.saved = False
        except ValueError as e:
            self.logger.warning(str(e))
            self.ui.show_warning("오류", str(e))
        except Exception as e:
            self.logger.error(f"Error in delete_highlight: {str(e)}")
            self.ui.show_error(f"하이라이트 삭제 중 오류: {str(e)}")

    def edit_match_time(self):
        try:
            message = self.timer_manager.edit_time(self.ui)
            if message:
                self.ui.update_status(message)
        except ValueError as e:
            self.logger.warning(str(e))
            self.ui.show_warning("입력 오류", str(e))
        except Exception as e:
            self.logger.error(f"Error in edit_match_time: {str(e)}")
            self.ui.show_error(f"타이머 시간 수정 중 오류: {str(e)}")

    def edit_highlight_inline(self):
        try:
            index = self.ui.get_selected_highlight_index()
            if index == -1:
                self.ui.show_info("알림", "수정할 하이라이트를 선택하세요.")
                return
            message = self.highlight_manager.edit(index, self.ui)
            self.ui.update_status(message)
            self.ui.update_highlights_view(self.highlight_manager.get_highlights())
            self.save_manager.saved = False
        except ValueError as e:
            self.logger.warning(str(e))
            self.ui.show_warning("입력 오류", str(e))
        except Exception as e:
            self.logger.error(f"Error in edit_highlight_inline: {str(e)}")
            self.ui.show_error(f"하이라이트 수정 중 오류: {str(e)}")

    def save_highlights(self):
        try:
            message = self.save_manager.save(self.highlight_manager.get_highlights())
            self.ui.update_status(message)
        except RuntimeError as e:
            self.logger.error(str(e))
            self.ui.show_error(str(e))
        except Exception as e:
            self.logger.error(f"Error in save_highlights: {str(e)}")
            self.ui.show_error(f"하이라이트 저장 중 오류: {str(e)}")

    def close_event(self, event):
        try:
            if self.save_manager.check_unsaved(self.highlight_manager.get_highlights()):
                event.accept()
            else:
                event.ignore()
        except Exception as e:
            self.logger.error(f"Error in close_event: {str(e)}")
            self.ui.show_error(f"프로그램 종료 중 오류: {str(e)}")
            event.ignore()

    def run(self):
        self.ui.show()
        sys.exit(self.app.exec_())

if __name__ == '__main__':
    try:
        app = HighlightRecorderApp()
        app.run()
    except Exception as e:
        print(f"Application failed to start: {str(e)}")
        raise