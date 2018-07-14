import logging
import sys

from PyQt5.QtWidgets import QApplication

from gui import GUI


def main():
    log = logging.getLogger('Tagger')
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

if __name__ == '__main__':
    main()