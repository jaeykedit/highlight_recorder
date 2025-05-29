from typing import List, Tuple, Optional
from models import Highlight
from commands import AddHighlightCommand, DeleteHighlightCommand, EditHighlightCommand
from PyQt5.QtWidgets import QInputDialog, QWidget
import logging

class HighlightManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.highlights: List[Highlight] = []
        self.highlight_start_time: Optional[int] = None

    def start_recording(self, current_time: int) -> str:
        try:
            if self.highlight_start_time is not None:
                raise ValueError("이미 하이라이트 기록이 시작되었습니다.")
            self.highlight_start_time = current_time
            return "하이라이트 기록 시작"
        except Exception as e:
            self.logger.error(f"Error starting highlight recording: {str(e)}")
            raise

    def stop_recording(self, current_time: int, memo: str) -> Tuple[Optional[AddHighlightCommand], Optional[str]]:
        try:
            if self.highlight_start_time is None:
                raise ValueError("하이라이트 기록이 시작되지 않았습니다.")
            if current_time < self.highlight_start_time:
                raise ValueError("종료 시간이 시작 시간보다 빠를 수 없습니다.")
            highlight = Highlight(self.highlight_start_time, current_time, memo)
            command = AddHighlightCommand(self, highlight)
            self.highlight_start_time = None
            return command, "하이라이트 기록 완료"
        except Exception as e:
            self.logger.error(f"Error stopping highlight recording: {str(e)}")
            raise

    def get_recording_status(self, current_time: int) -> Optional[dict]:
        try:
            if self.highlight_start_time is not None:
                duration = current_time - self.highlight_start_time
                start_min = self.highlight_start_time // 60
                start_sec = self.highlight_start_time % 60
                end_min = current_time // 60
                end_sec = current_time % 60
                return {
                    'start': f"{start_min:02}:{start_sec:02}",
                    'end': f"{end_min:02}:{end_sec:02}",
                    'duration': duration
                }
            return None
        except Exception as e:
            self.logger.error(f"Error getting recording status: {str(e)}")
            return None

    def add_highlight(self, highlight: Highlight):
        try:
            self.highlights.append(highlight)
            self.logger.debug("Highlight added: %s", highlight.to_display_string())
        except Exception as e:
            self.logger.error(f"Error adding highlight: {str(e)}")
            raise

    def delete(self, index: int) -> Tuple[Optional[DeleteHighlightCommand], Optional[str]]:
        try:
            if index < 0 or index >= len(self.highlights):
                raise ValueError("유효하지 않은 하이라이트 인덱스입니다.")
            command = DeleteHighlightCommand(self, index)
            return command, "하이라이트 삭제됨"
        except Exception as e:
            self.logger.error(f"Error deleting highlight: {str(e)}")
            raise

    def remove_highlight(self, index: int):
        try:
            if index < 0 or index >= len(self.highlights):
                raise ValueError("유효하지 않은 하이라이트 인덱스입니다.")
            self.highlights.pop(index)
            self.logger.debug("Highlight removed at index %d", index)
        except Exception as e:
            self.logger.error(f"Error removing highlight: {str(e)}")
            raise

    def edit(self, index: int, parent: QWidget) -> Tuple[Optional[EditHighlightCommand], Optional[str]]:
        try:
            if index < 0 or index >= len(self.highlights):
                raise ValueError("유효하지 않은 하이라이트 인덱스입니다.")
            highlight = self.highlights[index]
            memo, ok = QInputDialog.getText(parent, "하이라이트 수정", "새 메모를 입력하세요:", text=highlight.memo)
            if not ok:
                return None, "하이라이트 수정 취소"
            start_time_str, ok = QInputDialog.getText(parent, "하이라이트 수정", "시작 시간을 입력하세요 (MM:SS):", text=f"{highlight.raw_start // 60:02}:{highlight.raw_start % 60:02}")
            if not ok:
                return None, "하이라이트 수정 취소"
            try:
                start_min, start_sec = map(int, start_time_str.split(':'))
                start_time = start_min * 60 + start_sec
                end_time_str, ok = QInputDialog.getText(parent, "하이라이트 수정", "종료 시간을 입력하세요 (MM:SS):", text=f"{highlight.raw_end // 60:02}:{highlight.raw_end % 60:02}")
                if not ok:
                    return None, "하이라이트 수정 취소"
                end_min, end_sec = map(int, end_time_str.split(':'))
                end_time = end_min * 60 + end_sec
                if start_time < 0 or end_time < start_time:
                    raise ValueError("유효하지 않은 시간 범위입니다.")
                new_highlight = Highlight(start_time, end_time, memo)
                command = EditHighlightCommand(self, index, new_highlight)
                return command, "하이라이트 수정됨"
            except ValueError as e:
                parent.show_warning("입력 오류", f"잘못된 시간 형식입니다: {str(e)}")
                return None, ""
        except Exception as e:
            self.logger.error(f"Error editing highlight: {str(e)}")
            raise

    def update_highlight(self, index: int, new_highlight: Highlight):
        try:
            if index < 0 or index >= len(self.highlights):
                raise ValueError("유효하지 않은 하이라이트 인덱스입니다.")
            self.highlights[index] = new_highlight
            self.logger.debug("Highlight updated at index %d", index)
        except Exception as e:
            self.logger.error(f"Error updating highlight: {str(e)}")
            raise

    def get_highlights(self) -> List[Highlight]:
        try:
            return self.highlights
        except Exception as e:
            self.logger.error(f"Error getting highlights: {str(e)}")
            raise

    def restore_highlights(self, highlights: List[Highlight]):
        try:
            self.highlights = highlights
            self.highlight_start_time = None
            self.logger.debug("Highlights restored: %d highlights", len(highlights))
        except Exception as e:
            self.logger.error(f"Error restoring highlights: {str(e)}")
            raise