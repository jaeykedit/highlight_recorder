import sys
import time
import os
from typing import List, Dict
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit,
                             QLabel, QLineEdit, QFileDialog, QListWidget, QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt, QTimer, QMetaObject, Q_ARG, Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut
import keyboard
import logging
from highlight_saver import HighlightSaver
from models import Highlight

# 로깅 설정
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class HighlightRecorder(QWidget):
    def __init__(self):
        super().__init__()
        self.start_time = None
        self.running = False
        self.paused = False
        self.elapsed_time = 0
        self.match = 1
        self.saved = False
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_highlights)
        self.highlight_start_time = None
        self.highlights_by_match: Dict[int, List[Highlight]] = {1: []}
        self.record_button = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('하이라이트 메모 프로그램')
        layout = QVBoxLayout()

        self.timer_label = QLabel('00:00', self)
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(self.timer_label)

        self.status_label = QLabel('', self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; color: green;")
        layout.addWidget(self.status_label)

        self.memo_input = QLineEdit(self)
        self.memo_input.setPlaceholderText('하이라이트 설명 입력 (예: 1대4 클러치)')
        self.memo_input.returnPressed.connect(self.record_highlight)
        layout.addWidget(self.memo_input)

        self.start_button = QPushButton('매치 시작', self)
        self.start_button.clicked.connect(self.start_match)
        layout.addWidget(self.start_button)

        self.pause_button = QPushButton('타이머 일시정지', self)
        self.pause_button.clicked.connect(self.toggle_timer)
        layout.addWidget(self.pause_button)

        self.reset_button = QPushButton('타이머 초기화', self)
        self.reset_button.clicked.connect(self.reset_timer)
        layout.addWidget(self.reset_button)

        self.record_button = QPushButton('하이라이트 기록', self)
        self.record_button.clicked.connect(self.record_highlight)
        layout.addWidget(self.record_button)
        logging.debug("Record button explicitly initialized")

        self.new_match_button = QPushButton('새 매치', self)
        self.new_match_button.clicked.connect(self.new_match)
        layout.addWidget(self.new_match_button)

        self.edit_match_button = QPushButton('매치 번호 수정', self)
        self.edit_match_button.clicked.connect(self.edit_match_number)
        layout.addWidget(self.edit_match_button)

        self.edit_time_button = QPushButton('매치 시간 수정', self)
        self.edit_time_button.clicked.connect(self.edit_match_time)
        layout.addWidget(self.edit_time_button)

        self.delete_button = QPushButton('하이라이트 삭제', self)
        self.delete_button.clicked.connect(self.delete_highlight)
        layout.addWidget(self.delete_button)

        self.save_button = QPushButton('메모 저장', self)
        self.save_button.clicked.connect(self.save_highlights)
        layout.addWidget(self.save_button)

        if self.record_button is None:
            logging.error("Record button is None after initUI")
            raise RuntimeError("Failed to initialize record_button")

        self.highlights_view = QListWidget(self)
        self.highlights_view.itemDoubleClicked.connect(self.edit_highlight_inline)
        layout.addWidget(self.highlights_view)

        self.setLayout(layout)
        self.setFixedSize(400, 880)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

        # F1 핫키를 QShortcut로 대체하여 스레드 문제 방지
        self.f1_shortcut = QShortcut(QKeySequence('F1'), self)
        self.f1_shortcut.activated.connect(self.record_highlight)
        logging.debug("F1 shortcut registered with QShortcut")

        delete_shortcut = QShortcut(QKeySequence(Qt.Key_Delete), self)
        delete_shortcut.activated.connect(self.delete_highlight)

    def current_highlight_list(self):
        return self.highlights_by_match.setdefault(self.match, [])

    def start_match(self):
        try:
            if not self.running:
                self.start_time = time.time()
                self.running = True
                self.paused = False
                self.elapsed_time = 0
                self.timer.start(1000)
                self.auto_save_timer.start(60000)
                self.status_label.setText("매치 시작됨")
                logging.debug("Match started")
        except Exception as e:
            logging.error(f"Error in start_match: {str(e)}")
            QMessageBox.critical(self, "오류", f"매치 시작 중 오류: {str(e)}")

    def update_timer(self):
        try:
            if not self.paused:
                self.elapsed_time += 1
                minutes = self.elapsed_time // 60
                seconds = self.elapsed_time % 60
                self.timer_label.setText(f"{minutes:02}:{seconds:02}")
        except Exception as e:
            logging.error(f"Error in update_timer: {str(e)}")
            QMetaObject.invokeMethod(self, "show_error", Qt.QueuedConnection,
                                     Q_ARG(str, f"타이머 업데이트 중 오류: {str(e)}"))

    def toggle_timer(self):
        try:
            if self.running:
                self.paused = not self.paused
                self.pause_button.setText('타이머 재개' if self.paused else '타이머 일시정지')
                logging.debug(f"Timer {'paused' if self.paused else 'resumed'}")
        except Exception as e:
            logging.error(f"Error in toggle_timer: {str(e)}")
            QMetaObject.invokeMethod(self, "show_error", Qt.QueuedConnection,
                                     Q_ARG(str, f"타이머 토글 중 오류: {str(e)}"))

    def reset_timer(self):
        try:
            if self.running:
                self.elapsed_time = 0
                self.timer_label.setText("00:00")
                self.status_label.setText("타이머 초기화됨")
                self.highlight_start_time = None
                if self.record_button is None:
                    logging.error("record_button is None in reset_timer")
                    raise RuntimeError("Record button not initialized in reset_timer")
                self.record_button.setText('하이라이트 기록')
                logging.debug("record_button text set to '하이라이트 기록' in reset_timer")
        except Exception as e:

            logging.error(f"Error in reset_timer: {str(e)}")
            QMetaObject.invokeMethod(self, "show_error", Qt.QueuedConnection,
                                     Q_ARG(str, f"타이머 초기화 중 오류: {str(e)}"))

    def record_highlight(self):
        try:
            if not self.running:
                QMetaObject.invokeMethod(self, "show_warning", Qt.QueuedConnection,
                                         Q_ARG(str, "오류"), Q_ARG(str, "매치" \
                                         "를 먼저 시작하세요."))
                logging.warning("Attempted to record highlight without starting match")
                return

            if self.record_button is None:
                logging.error("record_button is None in record_highlight")
                QMetaObject.invokeMethod(self, "show_error", Qt.QueuedConnection,
                                         Q_ARG(str, "하이라이트 기록 버튼이 초기화되지 않았습니다."))
                return

            if self.highlight_start_time is None:
                self.highlight_start_time = self.elapsed_time
                minutes = self.highlight_start_time // 60
                seconds = self.highlight_start_time % 60
                self.status_label.setText(f"기록 시작: {minutes:02}:{seconds:02} (Recording...)")
                self.record_button.setText('기록 중지')
                self.memo_input.setFocus()
                logging.debug(f"Highlight recording started at {self.highlight_start_time}")
            else:
                raw_start = self.highlight_start_time
                raw_end = self.elapsed_time
                if raw_end <= raw_start:
                    QMetaObject.invokeMethod(self, "show_warning", Qt.QueuedConnection,
                                             Q_ARG(str, "오류"), Q_ARG(str, "하이라이트 기간은 0초보다 길어야 합니다."))
                    logging.warning("Highlight duration is zero or negative")
                    return

                memo = self.memo_input.text().strip() or '하이라이트'
                h = Highlight(raw_start, raw_end, memo)
                self.current_highlight_list().append(h)
                logging.debug(f"Recorded highlight: raw_start={raw_start}, raw_end={raw_end}, memo={memo}")
                if not any(self.highlights_view.item(i).text() == f"=== Match {self.match} ==="
                           for i in range(self.highlights_view.count())):
                    self.highlights_view.addItem(f"=== Match {self.match} ===")
                self.highlights_view.addItem(h.to_display_string())
                self.highlight_start_time = None
                self.memo_input.clear()
                self.status_label.setText("하이라이트 기록됨")
                self.record_button.setText('하이라이트 기록')
                self.saved = False
        except Exception as e:
            logging.error(f"Error in record_highlight: {str(e)}")
            QMetaObject.invokeMethod(self, "show_error", Qt.QueuedConnection,
                                     Q_ARG(str, f"하이라이트 기록 중 오류: {str(e)}"))

    def delete_highlight(self):
        try:
            selected_item = self.highlights_view.currentItem()
            if not selected_item:
                QMetaObject.invokeMethod(self, "show_info", Qt.QueuedConnection,
                                         Q_ARG(str, "알림"), Q_ARG(str, "삭제할 하이라이트를 선택하세요."))
                return

            selected_index_in_view = self.highlights_view.row(selected_item)
            highlight_list = self.current_highlight_list()
            actual_highlight_index = -1
            highlight_counter = 0

            for i in range(self.highlights_view.count()):
                if not self.highlights_view.item(i).text().startswith("==="):
                    if i == selected_index_in_view:
                        actual_highlight_index = highlight_counter
                        break
                    highlight_counter += 1

            if 0 <= actual_highlight_index < len(highlight_list):
                del highlight_list[actual_highlight_index]
                self.highlights_view.takeItem(selected_index_in_view)
                self.saved = False
                self.status_label.setText("하이라이트 삭제됨")
                logging.debug("Highlight deleted")
            else:
                QMetaObject.invokeMethod(self, "show_warning", Qt.QueuedConnection,
                                         Q_ARG(str, "오류"), Q_ARG(str, "선택된 하이라이트를 찾을 수 없습니다."))
                logging.warning("Could not find selected highlight to delete")
        except Exception as e:
            logging.error(f"Error in delete_highlight: {str(e)}")
            QMetaObject.invokeMethod(self, "show_error", Qt.QueuedConnection,
                                     Q_ARG(str, f"하이라이트 삭제 중 오류: {str(e)}"))

    def new_match(self):
        try:
            self.running = False
            self.paused = False
            self.timer.stop()
            self.elapsed_time = 0
            self.timer_label.setText("00:00")
            self.highlight_start_time = None
            if self.record_button is None:
                logging.error("record_button is None in new_match")
                raise RuntimeError("Record button not initialized in new_match")
            self.record_button.setText('하이라이트 기록')
            logging.debug("record_button text set to '하이라이트 기록' in new_match")
            
            self.match += 1
            self.highlights_by_match[self.match] = []
            self.highlights_view.addItem(f"=== Match {self.match} ===")
            self.status_label.setText(f"=== Match {self.match} ===")
            logging.debug(f"New match started: Match {self.match}")
        except Exception as e:
            logging.error(f"Error in new_match: {str(e)}")
            QMetaObject.invokeMethod(self, "show_error", Qt.QueuedConnection,
                                     Q_ARG(str, f"새 매치 생성 중 오류: {str(e)}"))

    def edit_match_number(self):
        try:
            new_match, ok = QInputDialog.getInt(self, '매치 번호 수정', '새 매치 번호를 입력하세요:', value=self.match, min=1)
            if ok:
                self.match = new_match
                self.highlights_by_match.setdefault(self.match, [])
                self.status_label.setText(f"=== Match {self.match} ===")
                logging.debug(f"Match number changed to {self.match}")
        except Exception as e:
            logging.error(f"Error in edit_match_number: {str(e)}")
            QMetaObject.invokeMethod(self, "show_error", Qt.QueuedConnection,
                                     Q_ARG(str, f"매치 번호 수정 중 오류: {str(e)}"))

    def edit_match_time(self):
        try:
            if self.running:
                new_time, ok = QInputDialog.getText(self, '매치 시간 수정', '새 경기 시간을 입력하세요 (MM:SS 형식):')
                if ok and new_time:
                    minutes, seconds = map(int, new_time.split(':'))
                    self.elapsed_time = minutes * 60 + seconds
                    self.timer_label.setText(f"{minutes:02}:{seconds:02}")
                    self.status_label.setText("시간 수정됨")
                    logging.debug(f"Match time edited to {minutes:02}:{seconds:02}")
        except ValueError:
            QMetaObject.invokeMethod(self, "show_warning", Qt.QueuedConnection,
                                     Q_ARG(str, "입력 오류"), Q_ARG(str, "올바른 형식(MM:SS)으로 입력하세요."))
            logging.warning("Invalid time format in edit_match_time")
        except Exception as e:
            logging.error(f"Error in edit_match_time: {str(e)}")
            QMetaObject.invokeMethod(self, "show_error", Qt.QueuedConnection,
                                     Q_ARG(str, f"매치 시간 수정 중 오류: {str(e)}"))

    def edit_highlight_inline(self):
        try:
            selected_item = self.highlights_view.currentItem()
            if not selected_item:
                QMetaObject.invokeMethod(self, "show_info", Qt.QueuedConnection,
                                         Q_ARG(str, "알림"), Q_ARG(str, "수정할 하이라이트를 선택하세요."))
                return

            new_text, ok = QInputDialog.getText(self, '하이라이트 수정', '내용을 수정하세요:', text=selected_item.text())
            if ok and new_text:
                selected_index_in_view = self.highlights_view.row(selected_item)
                highlight_list = self.current_highlight_list()
                actual_highlight_index = -1
                highlight_counter = 0

                for i in range(self.highlights_view.count()):
                    if not self.highlights_view.item(i).text().startswith("==="):
                        if i == selected_index_in_view:
                            actual_highlight_index = highlight_counter
                            break
                        highlight_counter += 1

                if 0 <= actual_highlight_index < len(highlight_list):
                    try:
                        time_part, memo = new_text.split(',', 1)
                        start_time, end_time = time_part.split('~')
                        start_min, start_sec = map(int, start_time.split(':'))
                        end_min, end_sec = map(int, end_time.split(':'))
                        raw_start = start_min * 60 + start_sec
                        raw_end = end_min * 60 + end_sec
                        highlight_list[actual_highlight_index] = Highlight(raw_start, raw_end, memo.strip())
                        selected_item.setText(new_text)
                        self.saved = False
                        self.status_label.setText("하이라이트 수정됨")
                        logging.debug("Highlight edited inline")
                    except ValueError:
                        QMetaObject.invokeMethod(self, "show_warning", Qt.QueuedConnection,
                                                 Q_ARG(str, "입력 오류"), Q_ARG(str, "올바른 형식(MM:SS~MM:SS, 메모)으로 입력하세요."))
                        logging.warning("Invalid format in edit_highlight_inline")
                else:
                    QMetaObject.invokeMethod(self, "show_warning", Qt.QueuedConnection,
                                             Q_ARG(str, "오류"), Q_ARG(str, "선택된 하이라이트를 찾을 수 없습니다."))
                    logging.warning("Could not find selected highlight to edit")
        except Exception as e:
            logging.error(f"Error in edit_highlight_inline: {str(e)}")
            QMetaObject.invokeMethod(self, "show_error", Qt.QueuedConnection,
                                     Q_ARG(str, f"하이라이트 수정 중 오류: {str(e)}"))

    def save_highlights(self):
        try:
            saver = HighlightSaver(self)
            success = saver.save_highlights(self.highlights_by_match)
            if success:
                self.saved = True
                self.status_label.setText("파일 저장됨")
                logging.debug("Highlights saved successfully")
        except Exception as e:
            logging.error(f"Error in save_highlights: {str(e)}")
            QMetaObject.invokeMethod(self, "show_error", Qt.QueuedConnection,
                                     Q_ARG(str, f"하이라이트 저장 중 오류: {str(e)}"))

    def auto_save_highlights(self):
        try:
            if not self.highlights_by_match:
                return
            os.makedirs('autosaves', exist_ok=True)
            with open('autosaves/highlights_autosave.txt', 'w', encoding='utf-8') as f:
                for m, lst in self.highlights_by_match.items():
                    for h in lst:
                        f.write(h.to_display_string() + '\n')
            logging.debug("Auto-save completed")
        except Exception as e:
            logging.error(f"Auto-save failed: {str(e)}")

    def closeEvent(self, event):
        try:
            if not any(self.highlights_by_match.values()) or self.saved:
                event.accept()
                return

            reply = QMessageBox.question(self, '종료 확인',
                                        '하이라이트가 저장되지 않았습니다. 저장 후 종료하시겠습니까?',
                                        QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.save_highlights()
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
            logging.debug("Close event handled")
        except Exception as e:
            logging.error(f"Error in closeEvent: {str(e)}")
            QMetaObject.invokeMethod(self, "show_error", Qt.QueuedConnection,
                                     Q_ARG(str, f"프로그램 종료 중 오류: {str(e)}"))

    # 에러 메시지 표시를 메인 스레드에서 처리
    def show_error(self, message):
        QMessageBox.critical(self, "오류", message)

    def show_warning(self, title, message):
        QMessageBox.warning(self, title, message)

    def show_info(self, title, message):
        QMessageBox.information(self, title, message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    recorder = HighlightRecorder()
    recorder.show()
    sys.exit(app.exec_())