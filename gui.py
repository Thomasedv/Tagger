import logging
import os.path
import time
import re
import sys
import traceback


import mutagen
import mutagen.mp3
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from mutagen.easyid3 import EasyID3

import utils
from table_widget import TableWidget
from rename_thread import Renamer


def capitalize(input_str):
    output = []
    for idx, letter in enumerate(input_str):
        try:
            if idx == 0:
                letter = letter.upper()
            elif input_str[idx - 1] in (' ', '.','-','(',')','[',']'):
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
    def __init__(self):
        super().__init__()

        folder = QFileDialog.getExistingDirectory()
        if not folder:
            sys.exit(1)
        self.folder_path = folder
        self.log = logging.getLogger('Tagger.gui')
        self.log.info('\n'+'-'*40)
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

        self.setStyleSheet(utils.stylesheet)
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

        self.log.debug('Showing window...')
        self.showMaximized()

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
        try:
            row = 0
            # self.items.insertRow(0)
            self.table.blockSignals(True)
            folder = os.listdir(self.folder_path)
            for full_file in folder:
                path = os.path.join(self.folder_path, full_file)
                if not os.path.isfile(path):
                    self.log.info(f'Ignored folder: {full_file}')
                    continue

                for idx, character in enumerate(reversed(full_file)):
                    if character == '.':
                        file, extension = full_file[:-idx - 1], full_file[-idx:]
                        # print(file, extension, sep='')
                        break
                else:
                    self.log.warning('Error on finding extension:', full_file)
                    continue
                # Added extension to set to widen support.

                if extension.lower() in ('mp3', 'wav', 'flac', 'ogg'):
                    title_item = QTableWidgetItem('')
                    artist_item = QTableWidgetItem('')

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

                    list_item = QTableWidgetItem(file)

                    list_item.setFlags(list_item.flags() ^ Qt.ItemIsEditable)

                    try:
                        self.table.setItem(row, 0, list_item)
                    except:
                         traceback.print_exc()
                    new_name = self.word_filter(file.lower())
                    new_name = capitalize(new_name)
                    new_fullfilename = ''.join((new_name, '.', extension))

                    count = 1
                    if new_fullfilename != full_file:
                        while new_fullfilename in folder:
                            self.log.info(f'New name already exists for {new_fullfilename}')
                            new_name = f'{new_name} ({count})'
                            new_fullfilename = ''.join((new_name, '.', extension))
                            count += 1

                    new_item = QTableWidgetItem(new_name)

                    # If a box was added.
                    if new_name.count(' - ') != 1 or count > 1:
                        new_item.setBackground(QColor('#e38c00'))

                    extension_item = QTableWidgetItem(extension.upper())
                    extension_item.setTextAlignment(Qt.AlignCenter)
                    extension_item.setFlags(extension_item.flags() ^ Qt.ItemIsEditable)
                    self.table.setItem(row, 1, new_item)
                    self.table.setItem(row, 2, extension_item)
                    self.table.setItem(row, 3, title_item)
                    self.table.setItem(row, 4, artist_item)

                    row += 1

        except Exception as e:
            print(e)
            traceback.print_exc()
        self.table.blockSignals(False)
        return row


if __name__ == '__main__':
    log = logging.getLogger('Tagger.gui')
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter('{name:<15}:{levelname:<7}: {message}', style="{")
    filehandler = logging.FileHandler('rename.log', encoding='utf-8')
    filehandler.setFormatter(formatter)
    filehandler.setLevel(logging.INFO)
    log.addHandler(filehandler)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    log.addHandler(ch)
    app = QApplication(sys.argv)
    qProcess = GUI()

    EXIT_CODE = app.exec_()
    log.info('Closing...')
