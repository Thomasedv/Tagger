import sys

from PyQt5.QtWidgets import QApplication

from gui import GUI
from utils import get_logger, FileHandler


def main():
    log = get_logger('Tagger')
    app = QApplication(sys.argv)
    file_handler = FileHandler()
    start_settings = file_handler.load_settings()
    qProcess = GUI(start_settings)
    EXIT_CODE = app.exec_()
    log.info('Saving and closing...')
    # Note: Use modified settings the GUI changes after use.
    file_handler.save_settings(qProcess.settings)
    # TODO: Add Tag All button.


if __name__ == '__main__':
    main()
