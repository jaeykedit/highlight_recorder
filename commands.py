from typing import List, Dict, Any
from models import Highlight
import logging

class Command:
    def execute(self):
        pass

    def undo(self):
        pass

    def redo(self):
        self.execute()

class RecordCommand(Command):
    def __init__(self, highlight_manager, highlight: Highlight):
        self.highlight_manager = highlight_manager
        self.highlight = highlight
        self.logger = logging.getLogger(__name__)

    def execute(self):
        self.highlight_manager.highlights.append(self.highlight)
        self.logger.debug(f"RecordCommand executed: {self.highlight}")

    def undo(self):
        if self.highlight in self.highlight_manager.highlights:
            self.highlight_manager.highlights.remove(self.highlight)
            self.logger.debug(f"RecordCommand undone: {self.highlight}")

class DeleteCommand(Command):
    def __init__(self, highlight_manager, index: int, highlight: Highlight):
        self.highlight_manager = highlight_manager
        self.index = index
        self.highlight = highlight
        self.logger = logging.getLogger(__name__)

    def execute(self):
        if 0 <= self.index < len(self.highlight_manager.highlights):
            self.highlight_manager.highlights.pop(self.index)
            self.logger.debug(f"DeleteCommand executed: index={self.index}")

    def undo(self):
        self.highlight_manager.highlights.insert(self.index, self.highlight)
        self.logger.debug(f"DeleteCommand undone: index={self.index}")

class EditCommand(Command):
    def __init__(self, highlight_manager, index: int, old_highlight: Highlight, new_highlight: Highlight):
        self.highlight_manager = highlight_manager
        self.index = index
        self.old_highlight = old_highlight
        self.new_highlight = new_highlight
        self.logger = logging.getLogger(__name__)

    def execute(self):
        if 0 <= self.index < len(self.highlight_manager.highlights):
            self.highlight_manager.highlights[self.index] = self.new_highlight
            self.logger.debug(f"EditCommand executed: index={self.index}")

    def undo(self):
        if 0 <= self.index < len(self.highlight_manager.highlights):
            self.highlight_manager.highlights[self.index] = self.old_highlight
            self.logger.debug(f"EditCommand undone: index={self.index}")

class EditTimeCommand(Command):
    def __init__(self, timer_manager, old_time: int, new_time: int, ui):
        self.timer_manager = timer_manager
        self.old_time = old_time
        self.new_time = new_time
        self.ui = ui
        self.logger = logging.getLogger(__name__)

    def execute(self):
        self.timer_manager.elapsed_time = self.new_time
        minutes = self.new_time // 60
        seconds = self.new_time % 60
        self.timer_manager.update_callback(minutes, seconds)
        self.logger.debug(f"EditTimeCommand executed: time={self.new_time}")

    def undo(self):
        self.timer_manager.elapsed_time = self.old_time
        minutes = self.old_time // 60
        seconds = self.old_time % 60
        self.timer_manager.update_callback(minutes, seconds)
        self.logger.debug(f"EditTimeCommand undone: time={self.old_time}")

class CommandManager:
    def __init__(self):
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.logger = logging.getLogger(__name__)

    def execute(self, command: Command):
        command.execute()
        self.undo_stack.append(command)
        self.redo_stack.clear()
        self.logger.debug("Command executed, undo stack size: %d", len(self.undo_stack))

    def undo(self):
        if not self.undo_stack:
            self.logger.debug("No commands to undo")
            return False
        command = self.undo_stack.pop()
        command.undo()
        self.redo_stack.append(command)
        self.logger.debug("Undo performed, redo stack size: %d", len(self.redo_stack))
        return True

    def redo(self):
        if not self.redo_stack:
            self.logger.debug("No commands to redo")
            return False
        command = self.redo_stack.pop()
        command.redo()
        self.undo_stack.append(command)
        self.logger.debug("Redo performed, undo stack size: %d", len(self.undo_stack))
        return True