#!/usr/bin/env python3
import sys
from PyQt5.Qt import QApplication

from MainDialog import MainDialog

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainDialog()
    window.show()
    sys.exit(app.exec())
