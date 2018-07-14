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