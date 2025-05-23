import os
import json
from typing import List, Dict, Any
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
        self.session_file = 'autosaves/session.json'

    def save(self, highlights: List[Highlight]) -> str:
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

    def save_session(self, timer_state: Dict[str, Any], highlights: List[Highlight], memo: str):
        try:
            os.makedirs('autosaves', exist_ok=True)
            session_data = {
                'timer': timer_state,
                'highlights': [
                    {'raw_start': h.raw_start, 'raw_end': h.raw_end, 'memo': h.memo}
                    for h in highlights
                ],
                'memo': memo,
                'saved': self.saved
            }
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            self.logger.debug("Session saved to %s", self.session_file)
        except Exception as e:
            self.logger.error("Failed to save session: %s", str(e))

    def load_session(self) -> Dict[str, Any]:
        try:
            if not os.path.exists(self.session_file):
                self.logger.debug("No session file found")
                return {}
            with open(self.session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.saved = data.get('saved', False)
            self.logger.debug("Session loaded from %s", self.session_file)
            return {
                'timer': data.get('timer', {}),
                'highlights': [
                    Highlight(h['raw_start'], h['raw_end'], h['memo'])
                    for h in data.get('highlights', [])
                ],
                'memo': data.get('memo', '')
            }
        except Exception as e:
            self.logger.error("Failed to load session: %s", str(e))
            if self.parent:
                self.parent.show_warning("세션 복구 실패", "세션 파일을 읽을 수 없습니다. 새 세션으로 시작합니다.")
            return {}