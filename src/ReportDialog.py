import os
from PyQt5 import uic
from PyQt5.Qt import QDialog

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


class ReportDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(CURRENT_DIR, 'ReportDialog.ui'), self)
        
    def exec(self):
        # TODO Вызвать метод setHtml в котором передать строку с html содержанием отчета 
        super().exec()

