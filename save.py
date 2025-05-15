import os
from typing import List
from PyQt5.QtWidgets import QMessageBox
from highlight_saver import HighlightSaver
from models import Highlight
import logging

class SaveManager:
    def __init__(self, parent):
        self.parent = parent
        self.saved = False
        self.logger = logging.getLogger(__name__)
        self.saver = HighlightSaver(parent)

    def save(self, highlights: List[Highlight]):
        if not highlights:
            self.logger.warning("No highlights to save")
            return "저장할 하이라이트가 없습니다."
        success = self.saver.save_highlights(highlights)
        if success:
            self.saved = True
            self.logger.debug("Highlights saved successfully")
            return "파일 저장됨"
        self.logger.error("Failed to save highlights")
        raise RuntimeError("하이라이트 저장 실패")

    def auto_save(self, highlights: List[Highlight]):
        if not highlights:
            return
        os.makedirs('autosaves', exist_ok=True)
        with open('autosaves/highlights_autosave.txt', 'w', encoding='utf-8') as f:
            for h in highlights:
                f.write(h.to_display_string() + '\n')
        self.logger.debug("Auto-save completed")

    def check_unsaved(self, highlights: List[Highlight]):
        if highlights and not self.saved:
            reply = QMessageBox.question(self.parent, '종료 확인',
                                        '하이라이트가 저장되지 않았습니다. 저장 후 종료하시겠습니까?',
                                        QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                        QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.save(highlights)
                return True
            elif reply == QMessageBox.No:
                return True
            return False
        return True