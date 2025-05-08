import sys
import time
import os
import csv
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit,
                             QLabel, QLineEdit, QFileDialog, QListWidget, QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
import keyboard

class HighlightRecorder(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.start_time = None
        self.running = False
        self.paused = False
        self.highlights = []
        self.match = 1
        self.elapsed_time = 0
        self.saved = False
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_highlights)
        self.highlight_start_time = None
        self.video_offset_seconds = 0
        self.highlights_raw = []
        self.highlights_offset = []

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

        self.pause_resume_button = QPushButton('타이머 일시정지', self)
        self.pause_resume_button.clicked.connect(self.toggle_timer)
        layout.addWidget(self.pause_resume_button)

        self.reset_timer_button = QPushButton('타이머 초기화', self)
        self.reset_timer_button.clicked.connect(self.reset_timer)
        layout.addWidget(self.reset_timer_button)

        self.record_button = QPushButton('하이라이트 기록', self)
        self.record_button.clicked.connect(self.record_highlight)
        layout.addWidget(self.record_button)

        self.new_match_button = QPushButton('새 매치', self)
        self.new_match_button.clicked.connect(self.new_match)
        layout.addWidget(self.new_match_button)

        self.edit_match_button = QPushButton('매치 번호 수정', self)
        self.edit_match_button.clicked.connect(self.edit_match_number)
        layout.addWidget(self.edit_match_button)

        self.edit_time_button = QPushButton('매치 시간 수정', self)
        self.edit_time_button.clicked.connect(self.edit_match_time)
        layout.addWidget(self.edit_time_button)

        self.set_offset_button = QPushButton('영상 오프셋 설정', self)
        self.set_offset_button.clicked.connect(self.set_video_offset)
        layout.addWidget(self.set_offset_button)

        self.delete_button = QPushButton('하이라이트 삭제', self)
        self.delete_button.clicked.connect(self.delete_highlight)
        layout.addWidget(self.delete_button)

        self.save_button = QPushButton('메모 저장', self)
        self.save_button.clicked.connect(self.save_highlights)
        layout.addWidget(self.save_button)

        self.highlights_view = QListWidget(self)
        self.highlights_view.itemDoubleClicked.connect(self.edit_highlight_inline)
        layout.addWidget(self.highlights_view)

        self.setLayout(layout)
        self.setFixedSize(400, 880)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

        keyboard.add_hotkey('f1', self.record_highlight)

    def set_video_offset(self):
        text, ok = QInputDialog.getText(self, '영상 오프셋 설정', '영상 상의 시작 시간 (MM:SS):')
        if ok and text:
            try:
                m, s = map(int, text.split(':'))
                self.video_offset_seconds = m * 60 + s - self.elapsed_time
                QMessageBox.information(self, '설정 완료', f'오프셋이 {self.video_offset_seconds}초로 설정되었습니다.')
            except:
                QMessageBox.warning(self, '입력 오류', '올바른 형식(MM:SS)으로 입력하세요.')

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

    def start_match(self):
        if not self.running:
            self.start_time = time.time()
            self.running = True
            self.paused = False
            self.elapsed_time = 0
            self.timer.start(1000)
            self.auto_save_timer.start(60000)
            if not self.highlights:
                self.add_highlight(f"=== Match {self.match} ===")

    def update_timer(self):
        if not self.paused:
            self.elapsed_time += 1
            minutes = self.elapsed_time // 60
            seconds = self.elapsed_time % 60
            self.timer_label.setText(f"{minutes:02}:{seconds:02}")

    def toggle_timer(self):
        if self.running:
            self.paused = not self.paused
            if self.paused:
                self.pause_resume_button.setText('타이머 재개')
            else:
                self.pause_resume_button.setText('타이머 일시정지')

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

                minutes_start, seconds_start = max(0, offset_start) // 60, max(0, offset_start) % 60
                minutes_end, seconds_end = max(0, offset_end) // 60, max(0, offset_end) % 60
                interval = f"{minutes_start:02}:{seconds_start:02}~{minutes_end:02}:{seconds_end:02}"
                memo = self.memo_input.text() if self.memo_input.text() else '하이라이트'
                highlight = f"{interval}, {memo}"
                raw_interval = f"{raw_start//60:02}:{raw_start%60:02}~{raw_end//60:02}:{raw_end%60:02}, {memo}"
                self.highlights.append(highlight)
                self.highlights_raw.append(raw_interval)
                self.highlights_offset.append((offset_start, offset_end, memo))
                self.highlights_view.addItem(highlight)
                self.highlight_start_time = None
                self.memo_input.clear()
                self.status_label.setText("")
                self.saved = False

    def new_match(self):
        self.match += 1
        self.reset_timer()
        self.add_highlight(f"\n=== Match {self.match} ===")

    def edit_match_number(self):
        new_match, ok = QInputDialog.getInt(self, '매치 번호 수정', '새 매치 번호를 입력하세요:', value=self.match, min=1)
        if ok:
            self.match = new_match
            self.add_highlight(f"\n=== Match {self.match} ===")

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

    def add_highlight(self, text):
        self.highlights.append(text)
        self.highlights_view.addItem(text)
        self.saved = False

    def edit_highlight_inline(self, item):
        new_text, ok = QInputDialog.getText(self, '하이라이트 수정', '내용을 수정하세요:', text=item.text())
        if ok and new_text:
            index = self.highlights_view.row(item)
            self.highlights[index] = new_text
            item.setText(new_text)
            self.saved = False

    def delete_highlight(self):
        selected_item = self.highlights_view.currentItem()
        if selected_item:
            reply = QMessageBox.question(self, '하이라이트 삭제', '정말 삭제하시겠습니까?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                index = self.highlights_view.row(selected_item)
                self.highlights.pop(index)
                self.highlights_view.takeItem(index)
                self.saved = False

    def save_highlights(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "메모 저장", "highlights.txt", "Text Files (*.txt)", options=options)
        if file_path:
            base_path = os.path.splitext(file_path)[0]
            with open(base_path + '_raw.txt', 'w', encoding='utf-8') as f:
                for item in self.highlights_raw:
                    f.write(item + '\n')
            with open(base_path + '_offset.txt', 'w', encoding='utf-8') as f:
                for item in self.highlights:
                    f.write(item + '\n')
            with open(base_path + '_markers.csv', 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
                writer.writerow(['Timecode In','Timecode Out','Name','Comment'])
                for start, end, memo in self.highlights_offset:
                    tc_in = f"{int(start)//3600:02}:{(int(start)%3600)//60:02}:{int(start)%60:02}:00"
                    tc_out = f"{int(end)//3600:02}:{(int(end)%3600)//60:02}:{int(end)%60:02}:00"
                    writer.writerow([tc_in, tc_out, memo, ''])

            # XML 생성 (60fps 기준)
            root = Element('xmeml')
            root.set('version', '5')
            project = SubElement(root, 'project')
            name = SubElement(project, 'name')
            name.text = '하이라이트 마커'
            sequence = SubElement(project, 'sequence')
            seq_name = SubElement(sequence, 'name')
            seq_name.text = f'Match {self.match}'
            duration = SubElement(sequence, 'duration')
            duration.text = '0'

            for start, end, memo in self.highlights_offset:
                marker = SubElement(sequence, 'marker')
                in_frame = SubElement(marker, 'in')
                in_frame.text = str(int(start * 60))  # 60fps
                out_frame = SubElement(marker, 'out')
                out_frame.text = str(int(end * 60))
                m_name = SubElement(marker, 'name')
                m_name.text = memo
                m_comment = SubElement(marker, 'comment')
                m_comment.text = memo

            xml_str = minidom.parseString(tostring(root)).toprettyxml(indent="  ")
            with open(base_path + '_markers.xml', 'w', encoding='utf-8') as f:
                f.write(xml_str)

            self.saved = True

    def auto_save_highlights(self):
        if self.highlights:
            os.makedirs('autosaves', exist_ok=True)
            with open('autosaves/highlights_autosave.txt', 'w', encoding='utf-8') as f:
                for item in self.highlights:
                    f.write(item + '\n')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    recorder = HighlightRecorder()
    recorder.show()
    sys.exit(app.exec_())
