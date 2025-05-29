import os
import json
import glob
from datetime import datetime
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
        self.session_dir = 'autosaves/sessions'
        self.max_sessions = 10

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
        try:
            os.makedirs('autosaves', exist_ok=True)
            with open('autosaves/highlights_autosave.txt', 'w', encoding='utf-8') as f:
                for h in highlights:
                    f.write(h.to_display_string() + '\n')
            self.logger.debug("Auto-save completed")
        except Exception as e:
            self.logger.error(f"Error in auto_save: {str(e)}")

    def check_unsaved(self, highlights: List[Highlight]):
        if highlights and not self.saved:
            try:
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
            except Exception as e:
                self.logger.error(f"Error checking unsaved: {str(e)}")
                return True
        return True

    def save_session(self, timer_state: Dict[str, Any], highlights: List[Highlight], memo: str):
        try:
            os.makedirs(self.session_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            session_file = os.path.join(self.session_dir, f'session_{timestamp}.json')
            session_data = {
                'timestamp': datetime.now().isoformat(),
                'highlight_count': len(highlights),
                'total_time': timer_state.get('elapsed_time', 0),
                'timer': timer_state,
                'highlights': [
                    {'raw_start': h.raw_start, 'raw_end': h.raw_end, 'memo': h.memo}
                    for h in highlights
                ],
                'memo': memo,
                'saved': self.saved
            }
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            self.logger.debug("Session saved to %s", session_file)
            self._limit_sessions()
        except Exception as e:
            self.logger.error(f"Failed to save session: {str(e)}")

    def load_session(self, session_file: str) -> Dict[str, Any]:
        try:
            if not os.path.exists(session_file):
                self.logger.debug("Session file not found: %s", session_file)
                return {}
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.saved = data.get('saved', False)
            self.logger.debug("Session loaded from %s", session_file)
            return {
                'timestamp': data.get('timestamp', ''),
                'highlight_count': data.get('highlight_count', 0),
                'total_time': data.get('total_time', 0),
                'timer': data.get('timer', {}),
                'highlights': [
                    Highlight(h['raw_start'], h['raw_end'], h['memo'])
                    for h in data.get('highlights', [])
                ],
                'memo': data.get('memo', '')
            }
        except Exception as e:
            self.logger.error(f"Failed to load session: {str(e)}")
            if self.parent:
                self.parent.show_warning("세션 복구 실패", "세션 파일을 읽을 수 없습니다. 새 세션으로 시작합니다.")
            return {}

    def list_sessions(self) -> List[Dict[str, Any]]:
        try:
            os.makedirs(self.session_dir, exist_ok=True)
            session_files = glob.glob(os.path.join(self.session_dir, 'session_*.json'))
            sessions = []
            for file in session_files:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    sessions.append({
                        'file': file,
                        'timestamp': data.get('timestamp', ''),
                        'highlight_count': data.get('highlight_count', 0),
                        'total_time': data.get('total_time', 0)
                    })
            sessions.sort(key=lambda x: x['timestamp'], reverse=True)
            self.logger.debug("Found %d sessions", len(sessions))
            return sessions
        except Exception as e:
            self.logger.error(f"Failed to list sessions: {str(e)}")
            return []

    def _limit_sessions(self):
        try:
            session_files = glob.glob(os.path.join(self.session_dir, 'session_*.json'))
            session_files.sort(key=lambda x: os.path.getmtime(x))
            while len(session_files) > self.max_sessions:
                oldest_file = session_files.pop(0)
                os.remove(oldest_file)
                self.logger.debug("Deleted old session file: %s", oldest_file)
        except Exception as e:
            self.logger.error(f"Failed to limit sessions: {str(e)}")

    def clear_session(self):
        try:
            if os.path.exists(self.session_dir):
                for file in glob.glob(os.path.join(self.session_dir, 'session_*.json')):
                    os.remove(file)
                self.logger.debug("All session files deleted")
            self.saved = False
        except Exception as e:
            self.logger.error(f"Error clearing sessions: {str(e)}")