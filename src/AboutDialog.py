import os
from PyQt5 import uic
# Далее импортировать все виджеты, используемые в главном окне приложения
# или выполнить импорт from PyQt5 import QtWidgets и обращаться к классам как QtWidgets.QMainWindow
from PyQt5.Qt import QDialog

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(CURRENT_DIR, 'AboutDialog.ui'), self)

