import os
import re
import sys
import traceback
from functools import wraps

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from utils import get_logger

log = get_logger('Tagger.Table')


def signal_blocker(func):
    """
    Wrapper that blocks signals while in the wrapped function.
    Keeps the block if it was there before the function was called.
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.signalsBlocked():
            keep_block = True
        else:
            keep_block = False
            self.blockSignals(True)

        func(self, *args, **kwargs)

        if not keep_block:
            self.blockSignals(False)

    return wrapper


class TableWidgetItem(QTableWidgetItem):
    def __lt__(self, other):
        return self.data(TableWidget.HANDLED_STATE) < other.data(TableWidget.HANDLED_STATE)


class TableWidget(QTableWidget):
    RENAMED = '2'
    DIVIDER = '1'
    UNHANDLED = '0'

    HANDLED_STATE = 32
    HANDLED_TIME = 33

    def __init__(self, folder, parent=None):
        super(TableWidget, self).__init__(parent=parent)

        self.folder_path = folder
        self.setCornerButtonEnabled(False)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)

        log.debug('Setting last edit state to None.')
        self.last_pre_edit_state = None

        self.undo_list = []
        self._was_checkout = False
        self.redo_list = []

        self.undo = QShortcut(QKeySequence('Ctrl+Z'), self)
        self.undo.activated.connect(self.undo_action)

        self.redo = QShortcut(QKeySequence('Ctrl+Shift+Z'), self)
        self.redo.activated.connect(self.redo_action)

        self.shortcut = QShortcut(QKeySequence('Ctrl+H'), self)
        self.shortcut.activated.connect(lambda: self.selectRow(2))
        # TODO: What if row 2 is non-existent?

        self.actions = {'Keep original': self.revert,
                        'Remove parentheses': self.remove_parentheses,
                        'Remove brackets': self.remove_brackets,
                        'Remove numbers': self.remove_numbers,
                        'Remove punctuation': self.remove_punctuation,
                        'Remove (Not delete)': self.delete_file,
                        'Swap positions': self.swap,
                        'Add tag(s)': self.create_tag,
                        'Play song': self.play_file,
                        'Checkout files': self.checkout_selection}

        self.cellDoubleClicked.connect(self.on_dclick_enter)
        self.cellChanged.connect(self._cell_change_handler)

    # def sortItems(self, p_int, order=Qt.AscendingOrder):
    #     print()

    def on_dclick_enter(self, row, col):
        if col != 1:
            return
        log.debug(f'Cell entered with double click at row: {row}.')
        self.last_pre_edit_state = self.item(row, col).text()
        log.debug(f'Last edit state set to: "{self.last_pre_edit_state}".')

    def _cell_change_handler(self, row, col):
        try:
            self.name_control([self.item(row, col)])
        except Exception as e:
            print(e)
        for iter_row in range(self.rowCount()):
            if (self.item(row, 1).text() == self.item(iter_row, 1).text()) and (row != iter_row):
                if self.item(row, 2).text() == self.item(iter_row, 2).text():
                    # print(self.item(row, 2).text())
                    # print(self.item(iter_row, 2).text())
                    self.alert_message('Note!', 'One song already has that name!', '')
                    self.item(row, 1).setText(self.last_pre_edit_state)

        if self.last_pre_edit_state == self.item(row, col).text():
            pass

        elif re.match(r'(^ *$)', self.item(row, 1).text()) is not None:
            self.item(row, col).setText(self.last_pre_edit_state)
            self.alert_message('Warning!','Invalid name!','The name can not be just spaces or nothing!')
        else:
            # print('Cell changed:', self.item(row, col).text())
            log.debug(f'Adding "{self.last_pre_edit_state}" to undo log.'
                      f' Current name is "{self.item(row, col).text()}"')

            self.undo_list.append(([self.item(row, col)], [self.last_pre_edit_state]))

    def _cell_action(self, action: str, items: list):
        # Find action, perform on each cell.
        try:
            self.blockSignals(True)

            self.actions[action](items)

            self.name_control([item for item in items if item.column() == 1])

            # print(items)
            # Restores from undo list, if a name already exists.
            # TODO: Make this comprehensible!
            for item in items:
                if item.column() == 1:
                    for iter_item in range(self.rowCount()):
                        if self.item(iter_item, 1) != item and item.text() == self.item(iter_item, 1).text():
                            if item.text() == self.item(iter_item, 2).text():

                                self.alert_message('Note!', f'One song already is already named {item.text()}!', '')
                                # a is the index of the item in the undo log.

                                a = next(i for i, v in zip(range(len(self.undo_list[-1][0]) - 1, -1, -1),
                                                           reversed(self.undo_list[-1][0])) if item == v)
                                self.undo_list[-1][0][a].setText(self.undo_list[-1][1][a])
                                # Removes the changed items from the undo log.
                                del self.undo_list[-1][0][a], self.undo_list[-1][1][a]

                        # print(a)
            self.blockSignals(False)
        except Exception as e:
            print(e)
            traceback.print_exc()

    def contextMenuEvent(self, event):
        items = self.selectedItems()
        # get the text inside selected cell (if any)
        menu = QMenu(self)
        # TODO: Rework menu to allow key shortcuts. Possibly, move to rename GUI.
        try:

            cursor = event.pos()
            index = self.indexAt(cursor)
            if self.itemFromIndex(index).data(TableWidget.HANDLED_STATE) == TableWidget.DIVIDER:
                return

            column = self.itemFromIndex(index).column()

            if column == 1:
                menu.addAction('Keep original')
                menu.addAction('Remove brackets')
                menu.addAction('Remove parentheses')
                menu.addAction('Remove punctuation')
                menu.addAction('Remove numbers')
                menu.addAction('Swap positions')
                menu.addSeparator()
            menu.addAction('Add tag(s)')
            menu.addAction('Checkout files')

            if len(items) == self.columnCount():
                play = menu.addAction('Play song')

            menu.addSeparator()
            menu.addAction('Remove (Not delete)')
        except:
            traceback.print_exc()

        action = menu.exec_(QCursor.pos())

        def not_divider(cell):
            return cell.data(TableWidget.HANDLED_STATE) != TableWidget.DIVIDER

        try:
            if action and action.text() == 'Play song':
                self.play_file([cell for cell in items if cell.column() in (0, 2)])
            elif action:
                self._cell_action(action.text(), [cell for cell in items if cell.column() == 1 and not_divider(cell)])
        except:
            traceback.print_exc()

    def keyPressEvent(self, event):
        key = event.key()
        # logging.debug(f'Keypress detected: {key}')
        if key == Qt.Key_Return and self.state() == QAbstractItemView.EditingState:
            modifier = QApplication.keyboardModifiers()

            item = self.currentItem()

            if Qt.ShiftModifier == modifier:
                if item.row() == 0:
                    return

                self.blockSignals(True)
                self.setCurrentCell(item.row() - 1, 1)
                self.editItem(self.item(item.row() - 1, 1))
                self.blockSignals(False)
                # Hack to call function on the enter of the next cell!
                self.cellChanged.emit(item.row(), 1)
                # Must go before cellChanged, or else, the last edit will be saved for the wrong box!
                self.cellDoubleClicked.emit(item.row() - 1, 1)

            else:
                if item.row() + 1 == self.rowCount():
                    return

                self.blockSignals(True)
                # Can close the editor.
                # self.closePersistentEditor(item)
                self.setCurrentCell(item.row() + 1, 1)
                self.editItem(self.item(item.row() + 1, 1))
                self.blockSignals(False)
                # Hack to call function on the enter of the next cell!
                self.cellChanged.emit(item.row(), 1)
                # Must go before cellChanged, or else, the last edit will be saved for the wrong box!
                self.cellDoubleClicked.emit(item.row() + 1, 1)

            # self.editItem(self.item(item.row()+2, 1))
        # elif key in (range(Qt.Key_A, Qt.Key_Z)):
        #    # Detect key range
        #    #logging.debug(f'Letter key pressed')
        else:
            modifier = QApplication.keyboardModifiers()
            if modifier == Qt.ControlModifier:
                super(TableWidget, self).keyPressEvent(event)
                # TODO: Implement elif that takes handles Shift + Home/End

            else:
                pass
            # logging.debug('Regular key detected, ignored input.')
            # super().keyPressEvent(event)

    def alert_message(self, title, text, info_text, question=False, allow_cancel=False):
        warning_window = QMessageBox(parent=self)
        warning_window.setText(text)
        warning_window.setIcon(QMessageBox.Warning)

        warning_window.setWindowTitle(title)

        if info_text:
            warning_window.setInformativeText(info_text)
        if question and allow_cancel:
            warning_window.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        elif question:
            warning_window.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        return warning_window.exec()

    @signal_blocker
    def undo_action(self):
        if not self.undo_list:
            return

        items, states = self.undo_list.pop()
        if isinstance(items, str):
            if items == TableWidget.RENAMED:
                self.redo_list.append((TableWidget.UNHANDLED, states.copy()))
            else:
                self.redo_list.append((TableWidget.RENAMED, states.copy()))

            for cell in states:
                cell.setData(TableWidget.HANDLED_STATE, items)
            self.sortItems(1, Qt.AscendingOrder)
        else:
            self.redo_list.append((items, [cell.text() for cell in items]))
            for cell, text in zip(items, states):
                cell.setText(text)

    @signal_blocker
    def redo_action(self):
        if not self.redo_list:
            return
        items, states = self.redo_list.pop()
        if isinstance(items, str):
            if items == TableWidget.RENAMED:
                self.undo_list.append((TableWidget.UNHANDLED, states.copy()))
            else:
                self.undo_list.append((TableWidget.RENAMED, states.copy()))

            for cell in states:
                cell.setData(TableWidget.HANDLED_STATE, items)
            self.sortItems(1, Qt.AscendingOrder)
        else:
            self.undo_list.append((items, [cell.text() for cell in items]))
            for cell, text in zip(items, states):
                cell.setText(text)

    @signal_blocker
    def name_control(self, items):
        # Potential for other post-prosessing options, like checking if it's different from the original str.
        # Does not call on cell edits, only on right-click actions.
        for cell in items:
            text = cell.text()
            text = re.sub(r'(^ +)', '', text)
            text = re.sub(r'( +)', ' ', text)
            text = re.sub(r'( +$)', '', text)

            if text.count(' - ') != 1:
                cell.setBackground(QColor('#e38c00'))
            else:
                cell.setBackground(QColor('#484848'))
            cell.setText(text)
            # if ' - ' in cell.text():
            #     cell.setBackground(QColor('#303030'))

    @signal_blocker
    def swap(self, items):
        self.undo_list.append((items, [cell.text() for cell in items]))
        cell_changed = False

        for cell in items:
            if cell.text().count(' - ') != 1:
                pass
            else:
                cell.setText(' - '.join(reversed(cell.text().split(' - '))))
                cell_changed = True

        if not cell_changed:
            self.undo_list.pop()

    @signal_blocker
    def revert(self, items):
        self.undo_list.append((items, [cell.text() for cell in items]))
        cell_changed = False

        for cell in items:
            original = self.item(cell.row(), 0)
            if original != cell.text():
                cell.setText(original.text())
                cell_changed = True

        if not cell_changed:
            self.undo_list.pop()

    @signal_blocker
    def remove_numbers(self, items):
        self.undo_list.append((items, [cell.text() for cell in items]))
        cell_changed = False

        for cell in items:
            text, changed = re.subn(r'[0-9]*', '', cell.text())
            if changed:
                cell.setText(text)
                cell_changed = True

        if not cell_changed:
            self.undo_list.pop()

    @signal_blocker
    def remove_parentheses(self, items):
        self.undo_list.append((items, [cell.text() for cell in items]))
        cell_changed = False
        for cell in items:
            text, changed = re.subn(r' *\([^)]*\) *', '', cell.text())
            text, changed_ = re.subn(r'[\(\)]', '', text)
            if changed or changed_:
                cell.setText(text)
                cell_changed = True

        if not cell_changed:
            self.undo_list.pop()

    @signal_blocker
    def remove_brackets(self, items):
        self.undo_list.append((items, [cell.text() for cell in items]))
        cell_changed = False

        for cell in items:
            text, changed = re.subn(r' *\[[^)]*\] *', '', cell.text())
            text, changed_ = re.subn(r'[\[\]]', '', text)
            if changed or changed_:
                cell.setText(text)
                cell_changed = True

        if not cell_changed:
            self.undo_list.pop()

    @signal_blocker
    def checkout_selection(self, items):
        self.undo_list.append((TableWidget.UNHANDLED, items))

        cell_changed = False

        for cell in items:
            cell.setData(TableWidget.HANDLED_STATE, TableWidget.RENAMED)
            cell_changed = True

        self.sortItems(1, Qt.AscendingOrder)
        if not cell_changed:
            self.undo_list.pop()

    @signal_blocker
    def remove_punctuation(self, items):
        self.undo_list.append((items, [cell.text() for cell in items]))
        cell_changed = False

        for cell in items:
            text, changed = re.subn(r'[.,\'\"]*', '', cell.text())
            if changed:
                cell.setText(text)
                cell_changed = True

        if not cell_changed:
            self.undo_list.pop()
    # TODO: Add tag -> Song name function
    # TODO: Add option to view log on rename errors.
    # TODO: Possibly let user swap columns for title/artist
    # TODO:

    @signal_blocker
    def delete_file(self, items):
        for cell in items:
            # os.remove()
            row = cell.row()
            self.removeRow(cell.row())
        del items[:]
        # print('Selecting row')
        self.selectRow(row)
        # print('Done selecting row')

    def play_file(self, items):
        # Recieves a list of items.
        path = os.path.join(self.folder_path, f'{items[0].text()}.{items[1].text().lower()}')
        log.info(f'Starting song at: {path}')
        if QDesktopServices.openUrl(QUrl.fromLocalFile(path)):
            log.info('Song start was successful!')
        else:
            log.warning('Failed to start song!')

    @signal_blocker
    def create_tag(self, items):
        self.undo_list.append((items, [cell.text() for cell in items]))
        cell_changed = False

        for item in items:
            if item.column() == 1:
                row = item.row()
                if item.text().count(' - ') == 1:
                    artist, title = item.text().split(' - ')
                    if title != self.item(row, 3).text() or \
                            artist != self.item(row, 4).text():
                        cell_changed = True
                        self.item(row, 3).setText(title)
                        self.item(row, 4).setText(artist)

        self.resizeColumnsToContents()
        self.resizeRowsToContents()

        horizontal_header = self.horizontalHeader()
        horizontal_header.setSectionResizeMode(0, QHeaderView.Stretch)
        horizontal_header.setSectionResizeMode(1, QHeaderView.Stretch)

        if not cell_changed:
            self.undo_list.pop()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    gui = TableWidget('test')
    gui.blockSignals(True)
    gui.setColumnCount(3)
    gui.insertRow(0)
    gui.insertRow(0)
    gui.insertRow(0)
    gui.setItem(0, 0, QTableWidgetItem('0'))
    gui.setItem(1, 0, QTableWidgetItem('0'))
    gui.setItem(2, 0, QTableWidgetItem('0'))
    gui.setItem(0, 1, QTableWidgetItem('0'))
    gui.blockSignals(False)
    gui.show()
    app.exec()
