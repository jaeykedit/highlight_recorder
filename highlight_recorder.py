# highlight_recorder.py (최신 전체 코드)
import sys
import time
import os
from dataclasses import dataclass
from typing import List
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit,
                             QLabel, QLineEdit, QFileDialog, QListWidget, QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut
import keyboard

@dataclass
class Highlight:
    raw_start: int
    raw_end: int
    offset_start: int
    offset_end: int
    memo: str

    def to_display_string(self):
        return f"{self.offset_start//60:02}:{self.offset_start%60:02}~{self.offset_end//60:02}:{self.offset_end%60:02}, {self.memo}"

    def to_raw_string(self):
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
        self.video_offset_seconds = 0
        self.highlights: List[Highlight] = []
        self.undo_stack: List[Highlight] = []

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
            ('영상 오프셋 설정', self.set_video_offset),
            ('하이라이트 삭제', self.delete_highlight),
            ('메모 저장', self.save_highlights)
        ]
        for text, func in buttons:
            btn = QPushButton(text, self)
            btn.clicked.connect(func)
            layout.addWidget(btn)

        self.highlights_view = QListWidget(self)
        self.highlights_view.itemDoubleClicked.connect(self.edit_highlight_inline)
        layout.addWidget(self.highlights_view)

        self.setLayout(layout)
        self.setFixedSize(400, 880)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

        keyboard.add_hotkey('f1', self.record_highlight)

        # 단축키 등록
        undo_shortcut = QShortcut(QKeySequence('Ctrl+Z'), self)
        undo_shortcut.activated.connect(self.undo_last_highlight)

        delete_shortcut = QShortcut(QKeySequence(Qt.Key_Delete), self)
        delete_shortcut.activated.connect(self.delete_highlight)

    def start_match(self):
        if not self.running:
            self.start_time = time.time()
            self.running = True
            self.paused = False
            self.elapsed_time = 0
            self.timer.start(1000)
            self.auto_save_timer.start(60000)

    def update_timer(self):
        if not self.paused:
            self.elapsed_time += 1
            minutes = self.elapsed_time // 60
            seconds = self.elapsed_time % 60
            self.timer_label.setText(f"{minutes:02}:{seconds:02}")

    def toggle_timer(self):
        if self.running:
            self.paused = not self.paused
            sender = self.sender()
            if sender:
                sender.setText('타이머 재개' if self.paused else '타이머 일시정지')

    def reset_timer(self):
        if self.running:
            self.elapsed_time = 0
            self.timer_label.setText("00:00")
            self.status_label.setText("")

    def record_highlight(self):
        if self.running:
            if self.highlight_start_time is None:
                self.highlight_start_time = self.elapsed_time
                minutes = self.highlight_start_time // 60
                seconds = self.highlight_start_time % 60
                self.status_label.setText(f"기록 시작 시간: {minutes:02}:{seconds:02}")
                self.memo_input.setFocus()
            else:
                raw_start = self.highlight_start_time
                raw_end = self.elapsed_time
                offset_start = raw_start + self.video_offset_seconds
                offset_end = raw_end + self.video_offset_seconds
                memo = self.memo_input.text() or '하이라이트'
                h = Highlight(raw_start, raw_end, offset_start, offset_end, memo)
                self.highlights.append(h)
                self.highlights_view.addItem(h.to_display_string())
                self.undo_stack.append(h)
                self.highlight_start_time = None
                self.memo_input.clear()
                self.status_label.setText("")
                self.saved = False

    def undo_last_highlight(self):
        if self.highlights:
            self.highlights.pop()
            self.highlights_view.takeItem(self.highlights_view.count() - 1)
            self.saved = False

    def delete_highlight(self):
        selected_item = self.highlights_view.currentItem()
        if selected_item:
            index = self.highlights_view.row(selected_item)
            del self.highlights[index]
            self.highlights_view.takeItem(index)
            self.saved = False

    def new_match(self):
        self.match += 1
        self.reset_timer()
        self.status_label.setText(f"=== Match {self.match} ===")

    def edit_match_number(self):
        new_match, ok = QInputDialog.getInt(self, '매치 번호 수정', '새 매치 번호를 입력하세요:', value=self.match, min=1)
        if ok:
            self.match = new_match
            self.status_label.setText(f"=== Match {self.match} ===")

    def edit_match_time(self):
        if self.running:
            new_time, ok = QInputDialog.getText(self, '매치 시간 수정', '새 경기 시간을 입력하세요 (MM:SS 형식):')
            if ok and new_time:
                try:
                    minutes, seconds = map(int, new_time.split(':'))
                    self.elapsed_time = minutes * 60 + seconds
                    self.timer_label.setText(f"{minutes:02}:{seconds:02}")
                except ValueError:
                    QMessageBox.warning(self, '입력 오류', '올바른 형식(MM:SS)으로 입력하세요.')

    def set_video_offset(self):
        text, ok = QInputDialog.getText(self, '영상 오프셋 설정', '영상 상의 시작 시간 (MM:SS):')
        if ok and text:
            try:
                m, s = map(int, text.split(':'))
                self.video_offset_seconds = m * 60 + s - self.elapsed_time
                QMessageBox.information(self, '설정 완료', f'오프셋이 {self.video_offset_seconds}초로 설정되었습니다.')
            except:
                QMessageBox.warning(self, '입력 오류', '올바른 형식(MM:SS)으로 입력하세요.')

    def edit_highlight_inline(self, item):
        new_text, ok = QInputDialog.getText(self, '하이라이트 수정', '내용을 수정하세요:', text=item.text())
        if ok and new_text:
            index = self.highlights_view.row(item)
            self.highlights_view.item(index).setText(new_text)
            self.saved = False

    def save_highlights(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "메모 저장", "highlights.txt", "Text Files (*.txt)", options=options)
        if file_path:
            base = os.path.splitext(file_path)[0]
            with open(base + '_raw.txt', 'w', encoding='utf-8') as f:
                for h in self.highlights:
                    f.write(h.to_raw_string() + '\n')
            with open(base + '_offset.txt', 'w', encoding='utf-8') as f:
                for h in self.highlights:
                    f.write(h.to_display_string() + '\n')
            root = Element('xmeml')
            root.set('version', '5')
            project = SubElement(root, 'project')
            name = SubElement(project, 'name')
            name.text = '하이라이트 마커'
            sequence = SubElement(project, 'sequence')
            SubElement(sequence, 'name').text = f'Match {self.match}'
            SubElement(sequence, 'duration').text = '0'
            for h in self.highlights:
                m = SubElement(sequence, 'marker')
                SubElement(m, 'in').text = str(int(h.offset_start * 60))
                SubElement(m, 'out').text = str(int(h.offset_end * 60))
                SubElement(m, 'name').text = h.memo
                SubElement(m, 'comment').text = h.memo
            xml_str = minidom.parseString(tostring(root)).toprettyxml(indent="  ")
            with open(base + '_markers.xml', 'w', encoding='utf-8') as f:
                f.write(xml_str)
            self.saved = True

    def auto_save_highlights(self):
        if self.highlights:
            os.makedirs('autosaves', exist_ok=True)
            with open('autosaves/highlights_autosave.txt', 'w', encoding='utf-8') as f:
                for h in self.highlights:
                    f.write(h.to_display_string() + '\n')

    def closeEvent(self, event):
        if self.highlights and not self.saved:
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
        else:
            event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    recorder = HighlightRecorder()
    recorder.show()
    sys.exit(app.exec_())
