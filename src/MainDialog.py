import jinja2
import os
import pwd
import secrets
import string
from PyQt5 import uic
# Далее импортировать все виджеты, используемые в главном окне приложения
# или выполнить импорт from PyQt5 import QtWidgets и обращаться к классам как QtWidgets.QMainWindow
from PyQt5.Qt import QApplication, QDialog, QMessageBox, QFileDialog

from AboutDialog import AboutDialog

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


def generate_password(length=8, require_letters=True, require_digits=True, require_punctuations=True):
    alphabet = ''
    punctuations = '!@#+%^*:;?-'
    if require_letters:
        alphabet = string.ascii_letters
    if require_digits:
        alphabet += string.digits
    if require_punctuations:
        alphabet += punctuations
    while True:
        password = "".join(secrets.choice(alphabet) for i in range(length))
        # Если в пароле д.б. символы, а их нет, то сгенерировать новый пароль
        if require_letters and not (set(string.ascii_letters) & set(password)):
            continue
        # Если в пароле д.б. цифры, а их нет, то сгенерировать новый пароль
        if require_digits and not (set(string.digits) & set(password)):
            continue
        # Если в пароле д.б. спец. символы, а их нет, то сгенерировать новый пароль
        if require_punctuations and not (set(punctuations) & set(password)):
            continue
        return password


class MainDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(CURRENT_DIR, 'MainDialog.ui'), self)

        self.aboutDialog = AboutDialog()

        self.environment = jinja2.Environment(loader=jinja2.FileSystemLoader(CURRENT_DIR))
        self.passwords = []
        self.users = []
        for entry in pwd.getpwall():
            if entry.pw_shell == '/bin/bash':
                self.users.append(entry.pw_name)

        self.genpassPagePushButton.clicked.connect(self.show_genpass_page)
        self.settingsPagePushButton.clicked.connect(self.show_settings_page)
        self.instpassPagePushButton.clicked.connect(self.show_instpass_page)
        self.genPassPushButton.clicked.connect(self.generate_passwords)
        self.instPassPushButton.clicked.connect(self.install_passwords)
        self.savePassToolButton.clicked.connect(self.save_passwords)
        self.copyPassToolButton.clicked.connect(self.copy_passwords)
        self.sellectAllCheckBox.clicked.connect(self.change_selection)
        self.aboutPushButton.clicked.connect(self.aboutDialog.exec)

        self.show_genpass_page()

    def generate_passwords(self):
        self.passwords = []
        for i in range(self.passCountSpinBox.value()):
            self.passwords.append(generate_password(int(self.symbolCountComboBox.currentText()),
                                                    self.latinCheckBox.isChecked(),
                                                    self.digitCheckBox.isChecked(),
                                                    self.specCheckBox.isChecked()))
        self.plainTextEdit.setPlainText("\n".join(self.passwords))
        self.sellectAllCheckBox.setChecked(False)

    def install_passwords(self):
        if QMessageBox.warning(self,
                               'Внимание!',
                               'Произойдет смена паролей для выбранных пользователей. Продолжить?',
                               QMessageBox.Yes | QMessageBox.No) == QMessageBox.No:
            return
        selected_text = self.plainTextEdit.textCursor().selectedText()
        print(selected_text)

    def save_passwords(self):
        filename, _ = QFileDialog.getSaveFileName(self, 'Сохранение паролей', '', "HTML (*.htm)")
        if not filename:
            return
        template = self.environment.get_template("passes.tmpl")
        content = template.render(passes="<br>".join(self.passwords))
        with open(filename, mode="w", encoding="utf-8") as message:
            message.write(content)

    def copy_passwords(self):
        clipboard = QApplication.clipboard()
        clipboard.setText("\n".join(self.passwords))

    def change_selection(self):
        if self.sellectAllCheckBox.isChecked():
            self.plainTextEdit.selectAll()
        else:
            cursor = self.plainTextEdit.textCursor()
            cursor.clearSelection()
            self.plainTextEdit.setTextCursor(cursor)

    def show_genpass_page(self):
        self.genpassPagePushButton.setDown(True)
        self.stackedWidget.setCurrentWidget(self.genPassPage)
        self.buttonsStackedWidget.setCurrentWidget(self.genPassButtonsPage)
        self.plainTextEdit.setPlainText("\n".join(self.passwords))
        self.sellectAllCheckBox.setChecked(False)

    def show_settings_page(self):
        self.settingsPagePushButton.setDown(True)
        self.stackedWidget.setCurrentWidget(self.settingsPage)

    def show_instpass_page(self):
        self.instpassPagePushButton.setDown(True)
        self.stackedWidget.setCurrentWidget(self.genPassPage)
        self.buttonsStackedWidget.setCurrentWidget(self.instPassButtonsPage)
        self.plainTextEdit.setPlainText("\n".join(self.users))
        self.sellectAllCheckBox.setChecked(False)
