from PySide2.QtWidgets import QApplication
from gui import MainWindow

if __name__ == '__main__':
    app = QApplication()
    app.setApplicationName("Symulator CT")

    w = MainWindow()
    w.show()

    exit(app.exec_())
