import os
import traceback

import mutagen
import mutagen.mp3
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from mutagen.easyid3 import EasyID3

from utils import get_logger


class Renamer(QThread):
    error = pyqtSignal(str)
    renamer_started = pyqtSignal(int, int)
    renamer_update = pyqtSignal(int)
    finished = pyqtSignal(tuple)

    def __init__(self, table, folder_path, parent=None):
        super(Renamer, self).__init__(parent)
        self.log = get_logger('Tagger.renamer')
        self.table = table
        self.folder_path = folder_path
        self.log.info('Rename thread initialized')

    def __del__(self):
        self.wait()

    def write_tags_to_files(self):
        """
        Applying tags to files, before renaming them.
        :return:
        :rtype:
        """
        try:
            tags_done = 0
            saves = []
            for row in range(self.table.rowCount()):
                title, artist = self.table.item(row, 3).text(), self.table.item(row, 4).text()
                if title == '' and artist == '':
                    continue
                file_ext = self.table.item(row, 2).text()
                filename = ''.join((self.table.item(row, 0).text(), '.', file_ext.lower()))
                path = os.path.join(self.folder_path, filename).replace('/', '\\')

                try:
                    meta = EasyID3(path)
                except mutagen.id3.ID3NoHeaderError:
                    meta = EasyID3()
                except Exception as e:
                    self.log.warning(f'Error happened when fetching metadata:\n{e}')
                    continue

                skip = False
                try:
                    if meta.keys():
                        if 'title' in meta.keys():
                            if title not in meta['title']:
                                meta['title'] = title
                            else:
                                skip = True
                        else:
                            meta['title'] = title

                        if 'artist' in meta.keys():
                            if artist not in meta['artist']:
                                meta['artist'] = artist
                            else:
                                if skip:
                                    continue
                        else:
                            meta['artist'] = artist
                    else:
                        meta['title'] = title
                        meta['artist'] = artist
                except Exception:
                    self.log.warning(f'Error on setting tag for {path}')
                    continue

                saves.append((meta, path))

            jobs = len(saves) * 2
            self.renamer_started.emit(0, jobs)

            tags_done = 0
            for meta, path in saves:
                try:
                    meta.save(path)
                    self.log.info(f'Tags saved for {path}')
                except PermissionError:
                    self.log.warning(f'Failed to save tags to file {path}')

                finally:
                    tags_done += 1
                    self.renamer_update.emit(tags_done)

        except Exception as e:
            traceback.print_exc()

        return tags_done

    def alert_message(self, title, text, info_text, question=False, allow_cancel=False):
        warning_window = QMessageBox(parent=None)
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

    def run(self):
        self.log.info('Starting renaming....\n{}'.format('-' * 40))
        # Pre-process check:
        renames = []
        old_names = set()

        tags_done = self.write_tags_to_files()

        # Preparing the renaming!
        # Creates a list with files to rename
        for row in range(self.table.rowCount()):
            file_ext = self.table.item(row, 2).text()
            filename = ''.join((self.table.item(row, 0).text(), '.', file_ext.lower()))
            new_filename = ''.join((self.table.item(row, 1).text(), '.', file_ext.lower()))

            if new_filename == '.' or file_ext == '':
                continue

            # print('-   |'+new_filename)

            if new_filename == filename:
                # print('No changes needed!', filename, '->', new_filename)
                # log.info(f'File "{filename}" has no changes!')
                continue
            else:
                old_names.add(filename)

            if new_filename in old_names:
                self.log.info(
                    f'File "{filename}" can\'t be renamed to "{new_filename}" since that name already exists!')
                # print(f'{filename} does already exist!')
                continue

            old_path = os.path.join(self.folder_path, filename).replace('/', '\\')
            new_path = os.path.join(self.folder_path, new_filename).replace('/', '\\')

            renames.append((old_path, new_path))
        # Emit number of renames!
        rename_length = len(renames)

        self.renamer_started.emit(rename_length, rename_length * 2)

        errors = 0
        step = rename_length
        for file in renames:
            try:
                os.rename(file[0], file[1])
                self.log.info(f'File successfully renamed: {file[0]} renamed to {file[1]}.')
            except PermissionError as e:
                errors += 1
                self.log.warning(f'Error: Renaming failed. '
                                 f'Did not get permission to edit file. Might be in use already.')
                self.log.debug(f'Full error: {e}')
                # traceback.print_exc()
            except FileExistsError as e:
                errors += 1
                self.log.warning(f'Error: Renaming failed. File {file} already exists!')
                self.log.debug(f'Full error: {e}')
            except Exception as e:
                errors += 1
                self.log.warning(f'An unexpected error was encountered renaming'
                                 f' {file[0]} to {file[1]}, with error:\n{e}')
                # print(e)
                # traceback.print_exc()

            # Emit progress
            step += 1
            self.renamer_update.emit(step)
        # print('Done!', f"{len(renames)} songs renamed, out of {self.table.rowCount()}")
        self.log.info(f'Renaming files complete, {rename_length - errors} of detected {rename_length} files renamed. '
                      f'Total files in table: {self.table.rowCount()}. Errors: {errors}')

        results = ('Renaming complete!',
                   'Renaming operation has been completed.',
                   f"{len(renames)-errors} songs has been renamed, out of {self.table.rowCount()} listed.\n"
                   f"{tags_done} tags have been applied. Encountered a total of {errors} errors!")

        self.finished.emit(results)
