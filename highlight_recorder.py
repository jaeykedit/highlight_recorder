import sys
import time
import os
from dataclasses import dataclass
from typing import List, Dict
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit,
                             QLabel, QLineEdit, QFileDialog, QListWidget, QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut
import keyboard
import logging
from highlight_saver import HighlightSaver  # 새 모듈 임포트

# 로깅 설정
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class Highlight:
    raw_start: int
    raw_end: int
    memo: str

    def to_display_string(self):
        return f"{self.raw_start//60:02}:{self.raw_start%60:02}~{self.raw_end//60:02}:{self.raw_end%60:02}, {self.memo}"

class HighlightRecorder(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
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

        buttons = [
            ('매치 시작', self.start_match),
            ('타이머 일시정지', self.toggle_timer),
            ('타이머 초기화', self.reset_timer),
            ('하이라이트 기록', self.record_highlight),
            ('새 매치', self.new_match),
            ('매치 번호 수정', self.edit_match_number),
            ('매치 시간 수정', self.edit_match_time),
            ('하이라이트 삭제', self.delete_highlight),
            ('메모 저장', self.save_highlights)
        ]
        for text, func in buttons:
            btn = QPushButton(text, self)
            btn.clicked.connect(func)
            if text == '하이라이트 기록':
                self.record_button = btn
            layout.addWidget(btn)

        self.highlights_view = QListWidget(self)
        self.highlights_view.itemDoubleClicked.connect(self.edit_highlight_inline)
        layout.addWidget(self.highlights_view)

        self.setLayout(layout)
        self.setFixedSize(400, 880)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

        keyboard.add_hotkey('f1', self.record_highlight)

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
            QMessageBox.critical(self, "오류", f"타이머 업데이트 중 오류: {str(e)}")

    def toggle_timer(self):
        try:
            if self.running:
                self.paused = not self.paused
                sender = self.sender()
                if sender:
                    sender.setText('타이머 재개' if self.paused else '타이머 일시정지')
                logging.debug(f"Timer {'paused' if self.paused else 'resumed'}")
        except Exception as e:
            logging.error(f"Error in toggle_timer: {str(e)}")
            QMessageBox.critical(self, "오류", f"타이머 토글 중 오류: {str(e)}")

    def reset_timer(self):
        try:
            if self.running:
                self.elapsed_time = 0
                self.timer_label.setText("00:00")
                self.status_label.setText("타이머 초기화됨")
                self.highlight_start_time = None
                self.record_button.setText('하이라이트 기록')
                logging.debug("Timer reset")
        except Exception as e:
            logging.error(f"Error in reset_timer: {str(e)}")
            QMessageBox.critical(self, "오류", f"타이머 초기화 중 오류: {str(e)}")

    def record_highlight(self):
        try:
            if not self.running:
                QMessageBox.warning(self, "오류", "매치를 먼저 시작하세요.")
                logging.warning("Attempted to record highlight without starting match")
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
                    QMessageBox.warning(self, "오류", "하이라이트 기간은 0초보다 길어야 합니다.")
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
            QMessageBox.critical(self, "오류", f"하이라이트 기록 중 오류: {str(e)}")

    def delete_highlight(self):
        try:
            selected_item = self.highlights_view.currentItem()
            if not selected_item:
                QMessageBox.information(self, "알림", "삭제할 하이라이트를 선택하세요.")
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
                QMessageBox.warning(self, "오류", "선택된 하이라이트를 찾을 수 없습니다.")
                logging.warning("Could not find selected highlight to delete")
        except Exception as e:
            logging.error(f"Error in delete_highlight: {str(e)}")
            QMessageBox.critical(self, "오류", f"하이라이트 삭제 중 오류: {str(e)}")

    def new_match(self):
        try:
            self.running = False
            self.paused = False
            self.timer.stop()
            self.elapsed_time = 0
            self.timer_label.setText("00:00")
            self.highlight_start_time = None
            self.record_button.setText('하이라이트 기록')
            
            self.match += 1
            self.highlights_by_match[self.match] = []
            self.highlights_view.addItem(f"=== Match {self.match} ===")
            self.status_label.setText(f"=== Match {self.match} ===")
            logging.debug(f"New match started: Match {self.match}")
        except Exception as e:
            logging.error(f"Error in new_match: {str(e)}")
            QMessageBox.critical(self, "오류", f"새 매치 생성 중 오류: {str(e)}")

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
            QMessageBox.critical(self, "오류", f"매치 번호 수정 중 오류: {str(e)}")

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
            QMessageBox.warning(self, '입력 오류', '올바른 형식(MM:SS)으로 입력하세요.')
            logging.warning("Invalid time format in edit_match_time")
        except Exception as e:
            logging.error(f"Error in edit_match_time: {str(e)}")
            QMessageBox.critical(self, "오류", f"매치 시간 수정 중 오류: {str(e)}")

    def edit_highlight_inline(self, item):
        try:
            new_text, ok = QInputDialog.getText(self, '하이라이트 수정', '내용을 수정하세요:', text=item.text())
            if ok and new_text:
                index = self.highlights_view.row(item)
                item.setText(new_text)
                self.saved = False
                self.status_label.setText("하이라이트 수정됨")
                logging.debug("Highlight edited inline")
        except Exception as e:
            logging.error(f"Error in edit_highlight_inline: {str(e)}")
            QMessageBox.critical(self, "오류", f"하이라이트 수정 중 오류: {str(e)}")

    def save_highlights(self):
        try:
            saver = HighlightSaver(self)  # HighlightSaver 인스턴스 생성
            success = saver.save_highlights(self.highlights_by_match)
            if success:
                self.saved = True
                self.status_label.setText("파일 저장됨")
                logging.debug("Highlights saved successfully")
        except Exception as e:
            logging.error(f"Error in save_highlights: {str(e)}")
            QMessageBox.critical(self, "저장 실패", f"하이라이트 저장 중 오류: {str(e)}")

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
            QMessageBox.critical(self, "오류", f"프로그램 종료 중 오류: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    recorder = HighlightRecorder()
    recorder.show()
    sys.exit(app.exec_())