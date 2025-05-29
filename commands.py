from typing import Optional, List
from models import Highlight
import logging

class Command:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def execute(self):
        pass

    def undo(self):
        pass

class CommandManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []

    def execute(self, command: Command) -> bool:
        try:
            command.execute()
            self.undo_stack.append(command)
            self.redo_stack.clear()
            self.logger.debug("Command executed: %s", command.__class__.__name__)
            return True
        except Exception as e:
            self.logger.error(f"Error executing command %s: %s", command.__class__.__name__, str(e))
            return False

    def undo(self) -> bool:
        try:
            if not self.undo_stack:
                return False
            command = self.undo_stack.pop()
            command.undo()
            self.redo_stack.append(command)
            self.logger.debug("Undo command: %s", command.__class__.__name__)
            return True
        except Exception as e:
            self.logger.error(f"Error undoing command: %s", str(e))
            return False

    def redo(self) -> bool:
        try:
            if not self.redo_stack:
                return False
            command = self.redo_stack.pop()
            command.execute()
            self.undo_stack.append(command)
            self.logger.debug("Redo command: %s", command.__class__.__name__)
            return True
        except Exception as e:
            self.logger.error(f"Error redoing command: %s", str(e))
            return False

class AddHighlightCommand(Command):
    def __init__(self, manager, highlight: Highlight):
        super().__init__()
        self.manager = manager
        self.highlight = highlight

    def execute(self):
        try:
            self.manager.add_highlight(self.highlight)
            self.logger.debug("AddHighlightCommand executed")
        except Exception as e:
            self.logger.error(f"Error in AddHighlightCommand execute: %s", str(e))
            raise

    def undo(self):
        try:
            index = len(self.manager.get_highlights()) - 1
            if index >= 0:
                self.manager.remove_highlight(index)
                self.logger.debug("AddHighlightCommand undone")
        except Exception as e:
            self.logger.error(f"Error in AddHighlightCommand undo: %s", str(e))
            raise

class DeleteHighlightCommand(Command):
    def __init__(self, manager, index: int):
        super().__init__()
        self.manager = manager
        self.index = index
        self.highlight: Optional[Highlight] = None

    def execute(self):
        try:
            self.highlight = self.manager.get_highlights()[self.index]
            self.manager.remove_highlight(self.index)
            self.logger.debug("DeleteHighlightCommand executed at index %d", self.index)
        except Exception as e:
            self.logger.error(f"Error in DeleteHighlightCommand execute: %s", str(e))
            raise

    def undo(self):
        try:
            if self.highlight is not None:
                self.manager.get_highlights().insert(self.index, self.highlight)
                self.logger.debug("DeleteHighlightCommand undone at index %d", self.index)
        except Exception as e:
            self.logger.error(f"Error in DeleteHighlightCommand undo: %s", str(e))
            raise

class EditHighlightCommand(Command):
    def __init__(self, manager, index: int, new_highlight: Highlight):
        super().__init__()
        self.manager = manager
        self.index = index
        self.new_highlight = new_highlight
        self.old_highlight: Optional[Highlight] = None

    def execute(self):
        try:
            self.old_highlight = self.manager.get_highlights()[self.index]
            self.manager.update_highlight(self.index, self.new_highlight)
            self.logger.debug("EditHighlightCommand executed at index %d", self.index)
        except Exception as e:
            self.logger.error(f"Error in EditHighlightCommand execute: %s", str(e))
            raise

    def undo(self):
        try:
            if self.old_highlight is not None:
                self.manager.update_highlight(self.index, self.old_highlight)
                self.logger.debug("EditHighlightCommand undone at index %d", self.index)
        except Exception as e:
            self.logger.error(f"Error in EditHighlightCommand undo: %s", str(e))
            raise

class EditTimeCommand(Command):
    def __init__(self, timer_manager, old_time: int, new_time: int):
        super().__init__()
        self.timer_manager = timer_manager
        self.old_time = old_time
        self.new_time = new_time

    def execute(self):
        try:
            self.timer_manager.set_time(self.new_time)
            self.logger.debug("EditTimeCommand executed: %d -> %d", self.old_time, self.new_time)
        except Exception as e:
            self.logger.error(f"Error in EditTimeCommand execute: %s", str(e))
            raise

    def undo(self):
        try:
            self.timer_manager.set_time(self.old_time)
            self.logger.debug("EditTimeCommand undone: %d -> %d", self.new_time, self.old_time)
        except Exception as e:
            self.logger.error(f"Error in EditTimeCommand undo: %s", str(e))
            raise