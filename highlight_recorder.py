import sys
import time
import os
from dataclasses import dataclass, field
from typing import List, Dict
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit,
                             QLabel, QLineEdit, QFileDialog, QListWidget, QInputDialog, QMessageBox)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut
from uuid import uuid4
import keyboard

@dataclass
class Highlight:
    raw_start: int
    raw_end: int
    memo: str

    def to_display_string(self):
        return f"{self.raw_start//60:02}:{self.raw_start%60:02}~{self.raw_end//60:02}:{self.raw_end%60:02}, {self.memo}"

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
        self.highlights_by_match: Dict[int, List[Highlight]] = {1: []}

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
                memo = self.memo_input.text() or '하이라이트'
                h = Highlight(raw_start, raw_end, memo)
                self.current_highlight_list().append(h)
                print(f"Recorded highlight: raw_start={raw_start}, raw_end={raw_end}, memo={memo}")  # 디버깅 로그
                if not any(self.highlights_view.item(i).text() == f"=== Match {self.match} ==="
                           for i in range(self.highlights_view.count())):
                    self.highlights_view.addItem(f"=== Match {self.match} ===")
                self.highlights_view.addItem(h.to_display_string())
                self.highlight_start_time = None
                self.memo_input.clear()
                self.status_label.setText("")
                self.saved = False

    def delete_highlight(self):
        selected_item = self.highlights_view.currentItem()
        if selected_item:
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
                    del highlight_list[actual_highlight_index]
                    item = self.highlights_view.takeItem(selected_index_in_view)
                    if item:
                        self.saved = False
                except IndexError:
                    QMessageBox.warning(self, "삭제 오류", "선택된 하이라이트 삭제 중 (내부 리스트 인덱스 오류).")
                except Exception as e:
                    QMessageBox.critical(self, "삭제 오류", f"하이라이트 삭제 중 예기치 않은 오류:\n{e}")
            else:
                QMessageBox.warning(self, "삭제 오류", "선택된 하이라이트가 유효하지 않거나 찾을 수 없습니다.")
        else:
            QMessageBox.information(self, "알림", "삭제할 하이라이트를 먼저 선택해주세요.")

    def new_match(self):
        self.match += 1
        self.reset_timer()
        self.highlights_by_match[self.match] = []
        self.highlights_view.addItem(f"=== Match {self.match} ===")
        self.status_label.setText(f"=== Match {self.match} ===")

    def edit_match_number(self):
        new_match, ok = QInputDialog.getInt(self, '매치 번호 수정', '새 매치 번호를 입력하세요:', value=self.match, min=1)
        if ok:
            self.match = new_match
            self.highlights_by_match.setdefault(self.match, [])
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

    def edit_highlight_inline(self, item):
        new_text, ok = QInputDialog.getText(self, '하이라이트 수정', '내용을 수정하세요:', text=item.text())
        if ok and new_text:
            index = self.highlights_view.row(item)
            item.setText(new_text)
            self.saved = False

    def save_highlights(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "메모 저장", "highlights.txt", "Text Files (*.txt)", options=options
        )
        if file_path:
            base = os.path.splitext(file_path)[0]
            try:
                with open(base + '_memo.txt', 'w', encoding='utf-8') as f:
                    for m, lst in self.highlights_by_match.items():
                        f.write(f"=== Match {m} ===\n\n")
                        for h in lst:
                            f.write(h.to_display_string() + '\n\n')
            except Exception as e:
                QMessageBox.critical(self, "저장 실패", f"메모 텍스트 저장 중 오류가 발생했습니다:\n{str(e)}")
                return
            for m, lst in self.highlights_by_match.items():
                try:
                    root = Element("xmeml")
                    root.set("version", "4")
                    sequence = SubElement(root, "sequence", {
                        "id": f"sequence_{m}",
                        "TL.SQAudioVisibleBase": "0",
                        "TL.SQVideoVisibleBase": "0",
                        "TL.SQVisibleBaseTime": "0",
                        "TL.SQAVDividerPosition": "0.5",
                        "TL.SQHideShyTracks": "0",
                        "TL.SQHeaderWidth": "292",
                        "Monitor.ProgramZoomOut": "0",
                        "Monitor.ProgramZoomIn": "0",
                        "TL.SQTimePerPixel": "0.2",
                        "MZ.EditLine": "0",
                        "MZ.Sequence.PreviewFrameSizeHeight": "1080",
                        "MZ.Sequence.PreviewFrameSizeWidth": "1920",
                        "MZ.Sequence.AudioTimeDisplayFormat": "200",
                        "MZ.Sequence.PreviewRenderingClassID": "1061109567",
                        "MZ.Sequence.PreviewRenderingPresetCodec": "1634755439",
                        "MZ.Sequence.PreviewRenderingPresetPath": "EncoderPresets/SequencePreview/795454d9-d3c2-429d-9474-923ab13b7018/QuickTime.epr",
                        "MZ.Sequence.PreviewUseMaxRenderQuality": "false",
                        "MZ.Sequence.PreviewUseMaxBitDepth": "false",
                        "MZ.Sequence.EditingModeGUID": "795454d9-d3c2-429d-9474-923ab13b7018",
                        "MZ.Sequence.VideoTimeDisplayFormat": "101",
                        "MZ.WorkOutPoint": "4612930560000",
                        "MZ.WorkInPoint": "0",
                        "explodedTracks": "true"
                    })
                    SubElement(sequence, "uuid").text = str(uuid4())
                    max_duration = max((h.raw_end for h in lst), default=1)
                    SubElement(sequence, "duration").text = str(int(max_duration * 60))
                    rate = SubElement(sequence, "rate")
                    SubElement(rate, "timebase").text = "60"
                    SubElement(rate, "ntsc").text = "FALSE"
                    SubElement(sequence, "name").text = f"Marker - (Match {m})"
                    media = SubElement(sequence, "media")
                    video = SubElement(media, "video")
                    format_elem = SubElement(video, "format")
                    samplecharacteristics = SubElement(format_elem, "samplecharacteristics")
                    rate = SubElement(samplecharacteristics, "rate")
                    SubElement(rate, "timebase").text = "60"
                    SubElement(rate, "ntsc").text = "FALSE"
                    codec = SubElement(samplecharacteristics, "codec")
                    SubElement(codec, "name").text = "Apple ProRes 422"
                    appspecificdata = SubElement(codec, "appspecificdata")
                    SubElement(appspecificdata, "appname").text = "Final Cut Pro"
                    SubElement(appspecificdata, "appmanufacturer").text = "Apple Inc."
                    SubElement(appspecificdata, "appversion").text = "7.0"
                    data = SubElement(appspecificdata, "data")
                    qtcodec = SubElement(data, "qtcodec")
                    SubElement(qtcodec, "codecname").text = "Apple ProRes 422"
                    SubElement(qtcodec, "codectypename").text = "Apple ProRes 422"
                    SubElement(qtcodec, "codectypecode").text = "apcn"
                    SubElement(qtcodec, "codecvendorcode").text = "appl"
                    SubElement(qtcodec, "spatialquality").text = "1024"
                    SubElement(qtcodec, "temporalquality").text = "0"
                    SubElement(qtcodec, "keyframerate").text = "0"
                    SubElement(qtcodec, "datarate").text = "0"
                    SubElement(samplecharacteristics, "width").text = "1920"
                    SubElement(samplecharacteristics, "height").text = "1080"
                    SubElement(samplecharacteristics, "anamorphic").text = "FALSE"
                    SubElement(samplecharacteristics, "pixelaspectratio").text = "square"
                    SubElement(samplecharacteristics, "fielddominance").text = "none"
                    SubElement(samplecharacteristics, "colordepth").text = "24"
                    track = SubElement(video, "track", {
                        "TL.SQTrackShy": "0",
                        "TL.SQTrackExpandedHeight": "25",
                        "TL.SQTrackExpanded": "0",
                        "MZ.TrackTargeted": "0"
                    })
                    SubElement(track, "enabled").text = "TRUE"
                    SubElement(track, "locked").text = "FALSE"
                    generatoritem = SubElement(track, "generatoritem", {"id": f"generatoritem_{m}"})
                    SubElement(generatoritem, "name").text = f"Marker Color Matte (Match {m})"
                    SubElement(generatoritem, "enabled").text = "TRUE"
                    SubElement(generatoritem, "duration").text = str(int(max_duration * 60))
                    rate = SubElement(generatoritem, "rate")
                    SubElement(rate, "timebase").text = "60"
                    SubElement(rate, "ntsc").text = "FALSE"
                    SubElement(generatoritem, "start").text = "0"
                    SubElement(generatoritem, "end").text = str(int(max_duration * 60))
                    SubElement(generatoritem, "in").text = "0"
                    SubElement(generatoritem, "out").text = str(int(max_duration * 60))
                    SubElement(generatoritem, "alphatype").text = "none"
                    effect = SubElement(generatoritem, "effect")
                    SubElement(effect, "name").text = "Color"
                    SubElement(effect, "effectid").text = "Color"
                    SubElement(effect, "effectcategory").text = "Matte"
                    SubElement(effect, "effecttype").text = "generator"
                    SubElement(effect, "mediatype").text = "video"
                    parameter = SubElement(effect, "parameter", {"authoringApp": "PremierePro"})
                    SubElement(parameter, "parameterid").text = "fillcolor"
                    SubElement(parameter, "name").text = "Color"
                    value = SubElement(parameter, "value")
                    SubElement(value, "alpha").text = "0"
                    SubElement(value, "red").text = "0"
                    SubElement(value, "green").text = "0"
                    SubElement(value, "blue").text = "0"
                    filter = SubElement(generatoritem, "filter")
                    effect = SubElement(filter, "effect")
                    SubElement(effect, "name").text = "Opacity"
                    SubElement(effect, "effectid").text = "opacity"
                    SubElement(effect, "effectcategory").text = "motion"
                    SubElement(effect, "effecttype").text = "motion"
                    SubElement(effect, "mediatype").text = "video"
                    SubElement(effect, "pproBypass").text = "false"
                    parameter = SubElement(effect, "parameter", {"authoringApp": "PremierePro"})
                    SubElement(parameter, "parameterid").text = "opacity"
                    SubElement(parameter, "name").text = "opacity"
                    SubElement(parameter, "valuemin").text = "0"
                    SubElement(parameter, "valuemax").text = "100"
                    SubElement(parameter, "value").text = "0"
                    seen_in_values = set()
                    for i, h in enumerate(lst):
                        in_value = int(h.raw_start * 60)
                        out_value = int(h.raw_end * 60)
                        if in_value > out_value:
                            print(f"Warning: Invalid marker range for highlight {i+1}: in={in_value}, out={out_value}")
                            out_value = in_value + 60  # Default to 1-second duration
                        while in_value in seen_in_values:
                            in_value += 1
                            out_value += 1
                        seen_in_values.add(in_value)
                        marker = SubElement(generatoritem, "marker")
                        SubElement(marker, "comment").text = h.memo
                        SubElement(marker, "name").text = ""
                        SubElement(marker, "in").text = str(in_value)
                        SubElement(marker, "out").text = str(out_value)
                        SubElement(marker, "pproColor").text = "4294741314"
                    timecode = SubElement(sequence, "timecode")
                    rate = SubElement(timecode, "rate")
                    SubElement(rate, "timebase").text = "60"
                    SubElement(rate, "ntsc").text = "FALSE"
                    SubElement(timecode, "string").text = "00:00:00:00"
                    SubElement(timecode, "frame").text = "0"
                    SubElement(timecode, "displayformat").text = "NDF"
                    labels = SubElement(sequence, "labels")
                    SubElement(labels, "label2").text = "Iris"
                    logginginfo = SubElement(sequence, "logginginfo")
                    SubElement(logginginfo, "description").text = ""
                    SubElement(logginginfo, "scene").text = ""
                    SubElement(logginginfo, "shottake").text = ""
                    SubElement(logginginfo, "lognote").text = ""
                    SubElement(logginginfo, "good").text = ""
                    SubElement(logginginfo, "originalvideofilename").text = ""
                    SubElement(logginginfo, "originalaudiofilename").text = ""
                    seen_in_values.clear()
                    for i, h in enumerate(lst):
                        in_value = int(h.raw_start * 60)
                        out_value = int(h.raw_end * 60)
                        if in_value > out_value:
                            print(f"Warning: Invalid marker range for highlight {i+1}: in={in_value}, out={out_value}")
                            out_value = in_value + 60
                        while in_value in seen_in_values:
                            in_value += 1
                            out_value += 1
                        seen_in_values.add(in_value)
                        marker = SubElement(sequence, "marker")
                        SubElement(marker, "comment").text = h.memo
                        SubElement(marker, "name").text = ""
                        SubElement(marker, "in").text = str(in_value)
                        SubElement(marker, "out").text = str(out_value)
                        SubElement(marker, "pproColor").text = "4294741314"
                    xml_str = minidom.parseString(tostring(root)).toprettyxml(indent="  ")
                    xml_path = f"{base}_markers_match_{m}.xml"
                    with open(xml_path, "w", encoding="utf-8") as f:
                        f.write(xml_str)
                except Exception as e:
                    QMessageBox.critical(self, "XML 저장 실패",
                                         f"Match {m}의 XML 저장 중 오류가 발생했습니다:\n{str(e)}")
                    return
            QMessageBox.information(self, "저장 완료", "모든 하이라이트가 성공적으로 저장되었습니다.")
            self.saved = True

    def auto_save_highlights(self):
        if self.highlights_by_match:
            os.makedirs('autosaves', exist_ok=True)
            with open('autosaves/highlights_autosave.txt', 'w', encoding='utf-8') as f:
                for m, lst in self.highlights_by_match.items():
                    for h in lst:
                        f.write(h.to_display_string() + '\n')

    def closeEvent(self, event):
        if not any(self.highlights_by_match.values()):
            event.accept()
        elif not self.saved:
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