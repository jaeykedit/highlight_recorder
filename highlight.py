from typing import List
from models import Highlight
import logging
from PyQt5.QtWidgets import QInputDialog

class HighlightManager:
    def __init__(self):
        self.highlights: List[Highlight] = []
        self.highlight_start_time = None
        self.logger = logging.getLogger(__name__)

    def start_recording(self, current_time):
        if self.highlight_start_time is None:
            self.highlight_start_time = current_time
            self.logger.debug(f"Highlight recording started at {current_time}")
            return f"기록 시작: {current_time//60:02}:{current_time%60:02} (Recording...)"
        return None

    def stop_recording(self, current_time, memo):
        if self.highlight_start_time is not None:
            raw_start = self.highlight_start_time
            raw_end = current_time
            if raw_end <= raw_start:
                self.logger.warning("Highlight duration is zero or negative")
                raise ValueError("하이라이트 기간은 0초보다 길어야 합니다.")
            memo = memo or '하이라이트'
            h = Highlight(raw_start, raw_end, memo)
            self.highlights.append(h)
            self.logger.debug(f"Recorded highlight: raw_start={raw_start}, raw_end={raw_end}, memo={memo}")
            self.highlight_start_time = None
            return "하이라이트 기록됨"
        return None

    def delete(self, index):
        if 0 <= index < len(self.highlights):
            deleted = self.highlights.pop(index)
            self.logger.debug(f"Highlight deleted: {deleted}")
            return "하이라이트 삭제됨"
        self.logger.warning("Invalid highlight index for deletion")
        raise ValueError("선택된 하이라이트를 찾을 수 없습니다.")

    def edit(self, index, parent):
        if 0 <= index < len(self.highlights):
            h = self.highlights[index]
            new_text, ok = QInputDialog.getText(parent, '하이라이트 수정', '내용을 수정하세요:',
                                                text=h.to_display_string())
            if ok and new_text:
                try:
                    time_part, memo = new_text.split(',', 1)
                    start_time, end_time = time_part.split('~')
                    start_min, start_sec = map(int, start_time.split(':'))
                    end_min, end_sec = map(int, end_time.split(':'))
                    raw_start = start_min * 60 + start_sec
                    raw_end = end_min * 60 + end_sec
                    self.highlights[index] = Highlight(raw_start, raw_end, memo.strip())
                    self.logger.debug(f"Highlight edited: index={index}, new_text={new_text}")
                    return "하이라이트 수정됨"
                except ValueError:
                    self.logger.warning("Invalid format in edit_highlight")
                    raise ValueError("올바른 형식(MM:SS~MM:SS, 메모)으로 입력하세요.")
        self.logger.warning("Invalid highlight index for edit")
        raise ValueError("선택된 하이라이트를 찾을 수 없습니다.")

    def get_highlights(self):
        return self.highlights