import json
import logging
import os

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


def get_logger(string):
    return logging.getLogger(string)


class FileHandler:
    """
    A class to handle loading/saving to files.
    """

    def __init__(self, settings='settings.json'):

        self.settings_path = settings
        self.work_dir = os.getcwd().replace('\\', '/')

    @staticmethod
    def is_file(path):
        return os.path.isfile(path) and os.access(path, os.X_OK)

    @staticmethod
    def find_file(relative_path, exist=True):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")

        path = os.path.join(base_path, relative_path).replace('\\', '/')

        if exist:
            if FileHandler.is_file(path):
                # print(f'Returning existing path: {path}')
                return path
            else:
                # print(f'No found: {relative_path}')
                return None

        else:
            # print(f'Returning path: {path}')
            return path

    def save_settings(self, settings):
        try:
            with open(self.settings_path, 'w') as f:
                json.dump(settings, f, indent=4, sort_keys=True)
                return True
        except (OSError, IOError) as e:
            # TODO: Logging!
            return False

    def load_settings(self, reset=False) -> dict:
        """ Reads settings, or writes them if absent, or if instructed to using reset. """

        def get_file(path):
            """  """
            if FileHandler.is_file(path):
                with open(path, 'r') as f:
                    return json.load(f)
            else:
                return {}

        if reset:
            return {}
        else:
            return get_file(self.settings_path)


def get_base_settings():
    pass


stylesheet = """
                QWidget {
                    background-color: #484848;
                    color: white;
                }
    
                QTabWidget::pane {
                    border: none;
                }
                
                QHeaderView::section, QTableCornerButton::section {
                    color: white;
                    background-color: #484848;
                    border: none;
                    padding: 2px;
                    border-bottom: 2px solid #303030;
                    border-left: 1px solid #303030;
                }
                
                QTableWidget {
                    gridline-color: #383838;
                    outline: 0;
                    selection-color: white;
                    selection-background-color: #383838;
                }
                
                QTableWidget::item:focus {
                    color: white;
                    background-color: #383838;
                }
                
                QMenu {
                    border: 1px solid #303030;
                }
                
                QMenu::item:selected {
                    background-color: #303030;
                }
    
                QMenu::item:disabled {
                    color: #808080;
                }
    
                QTabWidget {
                    background-color: #303030;
                }
    
                QTabBar {
                    background-color: #313131;
                }
    
                QTabBar::tab {
                    color: rgb(186,186,186);
                    background-color: #606060;
                    border-top-left-radius: 5px;
                    border-top-right-radius: 5px;
                    border-bottom: none;
                    min-width: 15ex;
                    min-height: 7ex;
                }
    
                QTabBar::tab:selected {
                    color: white;
                    background-color: #484848;
                }
                QTabBar::tab:!selected {
                    margin-top: 6px;
                }
    
                QTabWidget::tab-bar {
                    border-top: 1px solid #505050;
                }
    
                QLineEdit {
                    background-color: #303030;
                    color: rgb(186,186,186);
                    border-radius: none;
                    padding: 0 3px;
    
                }
                QLineEdit:disabled {
                    background-color: #303030;
                    color: #505050;
                    border-radius: 5px;
                }
    
                QTextEdit {
                    background-color: #484848;
                    color: rgb(186,186,186);
                    border: none;
                }
    
                QTextEdit#TextFileEdit {
                    background-color: #303030;
                    color: rgb(186,186,186);
                    border-radius: 5px;
                }
    
                QScrollBar:vertical {
                    border: none;
                    background-color: rgba(255,255,255,0);
                    width: 10px;
                    margin: 0px 0px 1px 0px;
                }
    
                QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
                    border: none;
                    background: none;
                }
    
                QScrollBar::handle:vertical {
                    background: #303030;
                    color: red;
                    min-height: 20px;
                    border-radius: 5px;
                }
    
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical  {
                    background: none;
                }
    
                QPushButton {
                    background-color: #303030;
                    color: white;
                    border: 1px grey;
                    border-radius: 5px;
                    border-style: solid;
                    width: 60px;
                    height: 20px;
                }
    
                QPushButton:disabled {
                    background-color: #484848;
                    color: grey;
                }
                QPushButton:pressed {
                    background-color: #101010;
                    color: white;
                }
                """
