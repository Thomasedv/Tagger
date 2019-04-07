import os.path
import re
import sys
import time

import mutagen
import mutagen.mp3
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from mutagen.easyid3 import EasyID3

from rename_thread import Renamer
from table_widget import TableWidget, TableWidgetItem
from utils import stylesheet, get_logger


def capitalize(input_str):
    output = []
    for idx, letter in enumerate(input_str):
        try:
            if idx == 0:
                letter = letter.upper()
            elif input_str[idx - 1] in (' ', '.', '-', '(', ')', '[', ']'):
                letter = letter.upper()
        except Exception as e:
            print(e)
        output.append(letter)

    return ''.join(output)


class WordFilter:
    def __init__(self, replace_dict: dict = None):
        if replace_dict is None:
            self.replace_dict = self.get_base_dict()
        else:
            self.replace_dict = replace_dict

        substrings = sorted(self.replace_dict, key=len, reverse=True)
        self.regexp = re.compile('|'.join(map(re.escape, substrings)))

    def get_base_dict(self):
        replace_dict = {
            '(lyrics)': '',
            '(lyric)': '',
            'lyric': '',
            'music': '',
            'video': '',
            ' hd': '',
            'lyrics': '',
            'audio': '',
            'with lyrics': '',
            ' hq': '',
            'switching vocals': '',
            '→': ' -',
            '  ': ' ',
            '_': '',
            '」': '',
            '「': '',
            '[animated]': '',
            '[ ~secret-nightcore~ edit ]': ''
        }
        return replace_dict

    def __call__(self, text):
        text = self.regexp.sub(lambda match: self.replace_dict[match.group(0)], text)
        text = re.sub(r'( +[-.,/\\]* +$)', '', text)
        text = re.sub(r'(^ +)', '', text)
        text = re.sub(r' +', ' ', text)
        return text

    def update_filter(self, replace_dict):
        self.replace_dict = replace_dict

    def get_replace_dict(self):
        return self.replace_dict


# TODO: Fix right click on wrong columns


class GUI(QMainWindow):

    def __init__(self, settings):
        super().__init__()
        self.settings = settings

        if 'folder' not in settings:
            self.settings['folder'] = QFileDialog.getExistingDirectory()
        folder = self.settings['folder']
        if not folder:
            sys.exit(1)

        self.folder_path = folder

        self.log = get_logger('Tagger.gui')
        self.log.info('\n' + '-' * 40)
        self.log.info(f'{time.strftime("%c")}')
        self.log.info(f'Starting... Current folder path "{self.folder_path}".')

        self.alert_icon_path = self.resource_path('Alert.ico')
        # self.window_icon_path = self.resource_path('icon.ico').replace('\\','/')
        self.alertIcon = QIcon()
        if self.alert_icon_path is None:
            self.log.warning(f'Did not find alert icon.')
        else:
            self.alertIcon.addFile(self.alert_icon_path)

        # TODO: Exception handling for tagging!
        # TODO: Add icons!

        # self.windowIcon = QIcon()
        # self.windowIcon.addFile(self.window_icon_path)

        # self.setWindowIcon(self.windowIcon)
        self.word_filter = WordFilter()
        self.setWindowTitle('Tagger')
        self.table = TableWidget(folder, parent=self)

        self.setStyleSheet(stylesheet)
        self.log.debug('Stylesheet set.')
        # self.items.setRowCount(4)

        self.table.setColumnCount(5)

        self.table.setHorizontalHeaderLabels(['Old name', 'New name', 'Filetype', 'Title', 'Artist'])
        self.table.horizontalHeader().setVisible(True)
        # self.items.verticalHeader().setVisible(False)
        self.log.debug('Fetching files and populating table...')
        self.get_names()
        self.log.debug('Table populated!')
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

        # self.table.resizeColumnsToContents()
        # self.table.resizeRowsToContents()

        horizontal_header = self.table.horizontalHeader()
        horizontal_header.setSectionResizeMode(0, QHeaderView.Stretch)
        horizontal_header.setSectionResizeMode(1, QHeaderView.Stretch)

        self.log.debug('Table resized to contents')

        # shortcut = QShortcut("Ctrl+N", self.items)
        # shortcut.em

        self.vertical_layout = QVBoxLayout()
        self.vertical_layout.addWidget(self.table)
        self.qwidget = QWidget(self)
        self.qwidget.setLayout(self.vertical_layout)
        self.setCentralWidget(self.qwidget)

        self.bottom_bar_layout = QHBoxLayout()
        self.rename_btn = QPushButton('Rename songs')
        self.rename_btn.setFixedWidth(self.rename_btn.fontMetrics().width(self.rename_btn.text()) + 10)
        self.rename_btn.clicked.connect(self.rename_songs)

        self.progressbar = QProgressBar(parent=self)

        self.bottom_bar_layout.addWidget(self.progressbar)
        self.bottom_bar_layout.addWidget(self.rename_btn)
        self.vertical_layout.addLayout(self.bottom_bar_layout)

        self.renamer = Renamer(self.table, folder, self)
        self.renamer.renamer_started.connect(self.started_renaming)
        self.renamer.renamer_update.connect(self.update_gui)
        self.renamer.finished.connect(self.rename_finished)

        bar = self.menuBar()
        file = bar.addMenu("File")
        set_folder = QAction("Select music folder", self)
        set_folder.triggered.connect(self.select_music_folder)
        file.addAction(set_folder)

        self.log.debug('Showing window...')
        self.showMaximized()

    def select_music_folder(self):
        # TODO: Make it save new folder, and reload GUI with new folder. Give warning when changing.
        self.log.info('Changing music folder!')
        pass

    @staticmethod
    def resource_path(relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """

        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")

        path = os.path.join(base_path, relative_path)

        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
        else:
            return None

    def alert_message(self, title, text, info_text, question=False, allow_cancel=False):
        warning_window = QMessageBox(parent=self)
        warning_window.setText(text)
        warning_window.setIcon(QMessageBox.Warning)
        warning_window.setWindowIcon(self.alertIcon)
        warning_window.setWindowTitle(title)

        if info_text:
            warning_window.setInformativeText(info_text)
        if question and allow_cancel:
            warning_window.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
        elif question:
            warning_window.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        return warning_window.exec()

    def rename_finished(self, results):
        self.alert_message(*results)
        # Reload table
        self.table.blockSignals(True)
        self.log.debug('Clearing table')
        self.table.clearContents()
        self.table.setRowCount(0)
        self.log.debug('Getting files in folder.')
        self.get_names()
        self.log.debug('Resizing to contents.')
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

        horizontal_header = self.table.horizontalHeader()
        horizontal_header.setSectionResizeMode(0, QHeaderView.Stretch)
        horizontal_header.setSectionResizeMode(1, QHeaderView.Stretch)

        self.table.blockSignals(False)
        self.log.debug('File renaming complete!\n{}'.format('-' * 40))

        self.table.setDisabled(False)
        self.progressbar.reset()
        self.rename_btn.setDisabled(False)

    def started_renaming(self, current, total):
        self.progressbar.setRange(0, total)
        self.progressbar.setValue(current)

    def update_gui(self, value):
        self.progressbar.setValue(value)

    def rename_songs(self):
        self.log.debug('Disabling table!')
        self.table.setDisabled(True)
        self.rename_btn.setDisabled(True)
        self.renamer.start()

    def get_names(self):
        old_col, new_col, ext_col, artist_col, title_col = range(5)
        row = 0

        # self.items.insertRow(0)
        self.table.blockSignals(True)

        # folder = os.listdir(self.folder_path)

        folder = sorted(os.listdir(self.folder_path), key=lambda x: os.path.getctime(os.path.join(self.folder_path, x)))
        for full_file in reversed(folder):
            path = os.path.join(self.folder_path, full_file)
            if not os.path.isfile(path):
                self.log.info(f'Ignored folder: {full_file}')
                continue

            # TODO: Use library to get exstention (os or pathlib)
            for idx, character in enumerate(reversed(full_file)):
                if character == '.':
                    file, extension = full_file[:-idx - 1], full_file[-idx:]
                    # print(file, extension, sep='')
                    break
            else:
                self.log.warning(f'Error on finding extension: {full_file}')
                continue

            # TODO: Introduce a supported files list
            if extension.lower() not in ('mp3', 'wav', 'flac', 'ogg'):
                continue
            title_item = TableWidgetItem('')
            artist_item = TableWidgetItem('')

            artist_item.setFlags(artist_item.flags() ^ Qt.ItemIsEditable)
            title_item.setFlags(title_item.flags() ^ Qt.ItemIsEditable)

            try:
                meta = EasyID3(path)
                if meta.keys():
                    if 'title' in meta.keys():
                        title_item.setText(meta['title'][0])
                    if 'artist' in meta.keys():
                        artist_item.setText(meta['artist'][0])
                else:
                    pass
                    # has_id_item.setBackground(QColor)
            except mutagen.id3.ID3NoHeaderError as e:
                self.log.info(e)
            except KeyError as e:
                self.log.info(f'{file} has no title/artist in tag.')

            self.table.insertRow(row)

            # Old column
            old_item = TableWidgetItem(file)
            old_item.setFlags(old_item.flags() ^ Qt.ItemIsEditable)

            # New column
            new_name = self.word_filter(file.lower())
            new_name = capitalize(new_name)
            new_filename = ''.join((new_name, '.', extension))

            count = 1
            if new_filename != full_file:
                while new_filename in folder:
                    self.log.info(f'New name already exists for {new_filename}')
                    new_name = f'{new_name} ({count})'
                    new_filename = ''.join((new_name, '.', extension))
                    count += 1

            new_item = TableWidgetItem(new_name)
            new_item.setData(TableWidget.HANDLED_STATE, TableWidget.UNHANDLED)
            # If a box was added.
            if new_name.count(' - ') != 1 or count > 1:
                new_item.setBackground(QColor('#e38c00'))

            # Extension column
            extension_item = TableWidgetItem(extension.upper())
            extension_item.setTextAlignment(Qt.AlignCenter)
            extension_item.setFlags(extension_item.flags() ^ Qt.ItemIsEditable)

            # Inserting to table
            self.table.setItem(row, old_col, old_item)
            self.table.setItem(row, new_col, new_item)
            self.table.setItem(row, ext_col, extension_item)
            self.table.setItem(row, title_col, title_item)
            self.table.setItem(row, artist_col, artist_item)

            row += 1

        def get_dummy(string=''):
            dummy = TableWidgetItem(string)
            dummy.setData(TableWidget.HANDLED_STATE, TableWidget.DIVIDER)
            dummy.setFlags(dummy.flags() ^ Qt.ItemIsEditable | Qt.ItemIsSelectable)
            dummy.setBackground(QColor('grey'))
            return dummy

        self.table.insertRow(row)

        self.table.setItem(row, old_col, get_dummy('RENAMED'))
        self.table.setItem(row, new_col, get_dummy())
        self.table.setItem(row, ext_col, get_dummy())
        self.table.setItem(row, title_col, get_dummy())
        self.table.setItem(row, artist_col, get_dummy())

        self.table.blockSignals(False)
        return row


if __name__ == '__main__':
    log = get_logger('Tagger.gui')

    app = QApplication(sys.argv)
    qProcess = GUI()

    EXIT_CODE = app.exec_()
    log.info('Closing...')
