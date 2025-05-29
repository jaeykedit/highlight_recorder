from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QListWidget, QMessageBox, QDialog, QDialogButtonBox
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut
from typing import List, Dict, Any
import logging

class HighlightRecorderUI(QWidget):
    def __init__(self, callbacks):
        super().__init__()
        try:
            self.logger = logging.getLogger(__name__)
            self.logger.debug("HighlightRecorderUI initializing")
            self.callbacks = callbacks
            self.init_ui()
            self.logger.debug("HighlightRecorderUI initialized successfully")
        except Exception as e:
            print(f"Error initializing HighlightRecorderUI: {str(e)}")
            raise

    def init_ui(self):
        try:
            self.setWindowTitle('하이라이트 메모 프로그램')
            layout = QVBoxLayout()

            # 시간 표시
            self.timer_label = QLabel('00:00', self)
            self.timer_label.setAlignment(Qt.AlignCenter)
            self.timer_label.setStyleSheet("font-size: 24px; font-weight: bold;")
            layout.addWidget(self.timer_label)

            # 상태 표시
            self.status_label = QLabel('', self)
            self.status_label.setAlignment(Qt.AlignCenter)
            self.status_label.setStyleSheet("font-size: 14px; color: green;")
            layout.addWidget(self.status_label)

            # 메모 입력
            self.memo_input = QLineEdit(self)
            self.memo_input.setPlaceholderText('하이라이트 설명 입력 (예: 1대4 클러치)')
            self.memo_input.returnPressed.connect(self.callbacks['record_highlight'])
            self.memo_input.setStyleSheet("font-size: 14px; padding: 5px;")
            layout.addWidget(self.memo_input)

            # 버튼
            buttons = [
                ('start_button', '타이머 시작', self.callbacks['start_match']),
                ('pause_button', '타이머 일시정지', self.callbacks['toggle_timer']),
                ('reset_button', '타이머 초기화', self.callbacks['reset_timer']),
                ('record_button', '하이라이트 기록', self.callbacks['record_highlight']),
                ('edit_time_button', '타이머 시간 수정', self.callbacks['edit_match_time']),
                ('delete_button', '하이라이트 삭제', self.callbacks['delete_highlight']),
                ('save_button', '메모 저장', self.callbacks['save_highlights']),
            ]
            for name, text, callback in buttons:
                button = QPushButton(text, self)
                button.clicked.connect(callback)
                button.setStyleSheet("padding: 8px;")
                setattr(self, name, button)
                layout.addWidget(button)

            # 하이라이트 목록
            self.highlights_view = QListWidget(self)
            self.highlights_view.itemDoubleClicked.connect(self.callbacks['edit_highlight'])
            self.highlights_view.setStyleSheet("font-size: 14px;")
            layout.addWidget(self.highlights_view)

            # Delete 단축키
            self.logger.debug("Registering Delete shortcut")
            delete_shortcut = QShortcut(QKeySequence(Qt.Key_Delete), self)
            delete_shortcut.activated.connect(self.callbacks['delete_highlight'])
            self.logger.debug("Delete shortcut registered")

            # Ctrl+S 단축키
            self.logger.debug("Registering Ctrl+S shortcut")
            save_shortcut = QShortcut(QKeySequence('Ctrl+S'), self)
            save_shortcut.activated.connect(self.callbacks['save_highlights'])
            self.logger.debug("Ctrl+S shortcut registered")

            # Ctrl+Z 단축키 (Undo)
            self.logger.debug("Registering Ctrl+Z shortcut")
            undo_shortcut = QShortcut(QKeySequence('Ctrl+Z'), self)
            undo_shortcut.activated.connect(self.callbacks['undo'])
            self.logger.debug("Ctrl+Z shortcut registered")

            # Ctrl+Shift+Z 단축키 (Redo)
            self.logger.debug("Registering Ctrl+Shift+Z shortcut")
            redo_shortcut = QShortcut(QKeySequence('Ctrl+Shift+Z'), self)
            redo_shortcut.activated.connect(self.callbacks['redo'])
            self.logger.debug("Ctrl+Shift+Z shortcut registered")

            self.setLayout(layout)
            self.setFixedSize(400, 800)
        except Exception as e:
            self.logger.error(f"Error in init_ui: {str(e)}")
            raise

    def show_session_selector(self, sessions: List[Dict[str, Any]]) -> str:
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("세션 선택")
            layout = QVBoxLayout()

            label = QLabel("복구할 세션을 선택하세요:", dialog)
            layout.addWidget(label)

            session_list = QListWidget(dialog)
            for session in sessions:
                timestamp = session['timestamp'].split('T')[0] + ' ' + session['timestamp'].split('T')[1][:8]
                total_time = session['total_time']
                time_str = f"{total_time // 60:02}:{total_time % 60:02}"
                item_text = f"{timestamp} | {session['highlight_count']} 하이라이트 | {time_str}"
                session_list.addItem(item_text)
            session_list.setCurrentRow(0)
            layout.addWidget(session_list)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, dialog)
            new_session_button = QPushButton("새 세션", dialog)
            buttons.addButton(new_session_button, QDialogButtonBox.ActionRole)
            layout.addWidget(buttons)

            selected_session = None

            def on_ok():
                nonlocal selected_session
                if session_list.currentRow() >= 0:
                    selected_session = sessions[session_list.currentRow()]['file']
                dialog.accept()

            def on_new_session():
                nonlocal selected_session
                selected_session = "new"
                dialog.accept()

            buttons.accepted.connect(on_ok)
            buttons.rejected.connect(dialog.reject)
            new_session_button.clicked.connect(on_new_session)

            dialog.setLayout(layout)
            result = dialog.exec_()

            if result == QDialog.Accepted:
                if selected_session == "new":
                    self.logger.debug("User chose to start new session")
                    return "new"
                elif selected_session:
                    self.logger.debug("User selected session: %s", selected_session)
                    return selected_session
            self.logger.debug("User cancelled session selection")
            return "cancel"
        except Exception as e:
            self.logger.error(f"Error in show_session_selector: {str(e)}")
            return "cancel"

    def ask_session_restore(self) -> str:
        try:
            reply = QMessageBox.question(
                self,
                '세션 복구',
                '이전 세션을 복구하시겠습니까?',
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.logger.debug("User chose to restore previous session")
                return "restore"
            elif reply == QMessageBox.No:
                self.logger.debug("User chose to start new session")
                return "new"
            else:
                self.logger.debug("User cancelled session selection")
                return "cancel"
        except Exception as e:
            self.logger.error(f"Error in ask_session_restore: {str(e)}")
            return "cancel"

    @pyqtSlot(str)
    def show_error(self, message):
        QMessageBox.critical(self, "오류", message)

    @pyqtSlot(str, str)
    def show_warning(self, title, message):
        QMessageBox.warning(self, title, message)

    @pyqtSlot(str, str)
    def show_info(self, title, message):
        QMessageBox.information(self, title, message)

    def update_timer_display(self, minutes, seconds):
        self.timer_label.setText(f"{minutes:02}:{seconds:02}")

    def update_status(self, message):
        self.status_label.setText(message)

    def update_highlights_view(self, highlights):
        self.highlights_view.clear()
        for h in highlights:
            self.highlights_view.addItem(h.to_display_string())

    def clear_memo(self):
        self.memo_input.clear()

    def get_memo(self):
        return self.memo_input.text().strip()

    def get_selected_highlight_index(self):
        selected_item = self.highlights_view.currentItem()
        return self.highlights_view.row(selected_item) if selected_item else -1