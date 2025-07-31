import os
from PyQt5 import uic
from PyQt5.Qt import QDialog

import resources

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


class ReportDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(CURRENT_DIR, 'ReportDialog.ui'), self)
        
    def exec(self, report):
        self.textEdit.setHtml(report)
        super().exec()

