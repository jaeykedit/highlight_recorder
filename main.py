import sys
import logging
import atexit
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from ui import HighlightRecorderUI
from timer import TimerManager
from highlight import HighlightManager
from save import SaveManager
from commands import CommandManager
import os

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
            self.command_manager = CommandManager()
            callbacks = {
                'start_match': self.start_match,
                'toggle_timer': self.toggle_timer,
                'reset_timer': self.reset_timer,
                'record_highlight': self.record_highlight,
                'edit_match_time': self.edit_match_time,
                'delete_highlight': self.delete_highlight,
                'edit_highlight': self.edit_highlight_inline,
                'save_highlights': self.save_highlights,
                'undo': self.undo,
                'redo': self.redo,
            }
            self.ui = HighlightRecorderUI(callbacks)
            self.save_manager.parent = self.ui
            self.ui.closeEvent = self.close_event
            atexit.register(self.save_session)
            if not self.handle_session_choice():
                self.logger.debug("Application startup cancelled")
                sys.exit(0)
            self.logger.debug("HighlightRecorderApp initialized successfully")
        except Exception as e:
            print(f"Error initializing HighlightRecorderApp: {str(e)}")
            raise

    def handle_session_choice(self) -> bool:
        try:
            if os.path.exists('autosaves/session.json'):
                choice = self.ui.ask_session_restore()
                if choice == "restore":
                    self.load_session()
                elif choice == "new":
                    self.save_manager.clear_session()
                    self.ui.update_status("새 세션 시작")
                elif choice == "cancel":
                    return False
            else:
                self.ui.update_status("새 세션 시작")
            return True
        except Exception as e:
            self.logger.error(f"Error handling session choice: {str(e)}")
            self.ui.show_error(f"세션 선택 중 오류: {str(e)}")
            return False

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
                command, message = self.highlight_manager.stop_recording(current_time, memo)
                if command and message:
                    self.command_manager.execute(command)
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
            command, message = self.highlight_manager.delete(index)
            if command and message:
                self.command_manager.execute(command)
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
            command, message = self.timer_manager.edit_time(self.ui, self.ui)
            if command and message:
                self.command_manager.execute(command)
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
            command, message = self.highlight_manager.edit(index, self.ui)
            if command and message:
                self.command_manager.execute(command)
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

    def undo(self):
        try:
            if self.command_manager.undo():
                self.ui.update_highlights_view(self.highlight_manager.get_highlights())
                self.ui.update_status("실행 취소됨")
                self.save_manager.saved = False
            else:
                self.ui.update_status("취소할 작업이 없습니다")
        except Exception as e:
            self.logger.error(f"Error in undo: {str(e)}")
            self.ui.show_error(f"실행 취소 중 오류: {str(e)}")

    def redo(self):
        try:
            if self.command_manager.redo():
                self.ui.update_highlights_view(self.highlight_manager.get_highlights())
                self.ui.update_status("다시 실행됨")
                self.save_manager.saved = False
            else:
                self.ui.update_status("다시 실행할 작업이 없습니다")
        except Exception as e:
            self.logger.error(f"Error in redo: {str(e)}")
            self.ui.show_error(f"다시 실행 중 오류: {str(e)}")

    def save_session(self):
        try:
            timer_state = self.timer_manager.get_state()
            highlights = self.highlight_manager.get_highlights()
            memo = self.ui.get_memo()
            self.save_manager.save_session(timer_state, highlights, memo)
        except Exception as e:
            self.logger.error(f"Error saving session: {str(e)}")

    def load_session(self):
        try:
            session_data = self.save_manager.load_session()
            if not session_data:
                return
            # 타이머 복원
            timer_data = session_data.get('timer', {})
            self.timer_manager.restore_state(timer_data)
            if timer_data.get('running', False) and not timer_data.get('paused', False):
                self.timer_manager.start()
                self.ui.pause_button.setText('타이머 일시정지')
            elif timer_data.get('paused', False):
                self.ui.pause_button.setText('타이머 재개')
            # 하이라이트 복원
            highlights = session_data.get('highlights', [])
            self.highlight_manager.restore_highlights(highlights)
            self.ui.update_highlights_view(highlights)
            # 메모 복원
            memo = session_data.get('memo', '')
            self.ui.memo_input.setText(memo)
            self.ui.update_status("이전 세션 복구됨")
        except Exception as e:
            self.logger.error(f"Error loading session: {str(e)}")
            self.ui.show_warning("세션 복구 실패", "세션 복구에 실패했습니다. 새 세션으로 시작합니다.")

    def close_event(self, event):
        try:
            self.save_session()
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