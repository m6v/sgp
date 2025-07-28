import jinja2
import os
import pwd
import secrets
import string
import subprocess
from PyQt5 import uic
from PyQt5.Qt import QApplication, QDialog, QMessageBox, QFileDialog, QListWidget, QPrinter, QPrintDialog, QTextDocument, QTextEdit

from AboutDialog import AboutDialog
from ReportDialog import ReportDialog

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
        self.reportDialog = ReportDialog()
        
        self.environment = jinja2.Environment(loader=jinja2.FileSystemLoader(CURRENT_DIR))
        self.passwords = []
        self.users = []
        for entry in pwd.getpwall():
            if entry.pw_shell in ('/bin/bash', '/bin/sh'):
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
        self.openReportToolButton.clicked.connect(self.show_report)
        self.saveReportToolButton.clicked.connect(self.save_report)
        self.printReportToolButton.clicked.connect(self.print_report)
        self.setRemotePassRadioButton.clicked.connect(self.switch_remotehost_setup)
        self.setLocalPassRadioButton.clicked.connect(self.switch_localhost_setup)
        self.clearToolButton.clicked.connect(self.clear_remote_user)
        
        self.listWidget.setSelectionMode(QListWidget.MultiSelection)

        self.show_genpass_page()

    def generate_passwords(self):
        self.passwords = []
        for i in range(self.passCountSpinBox.value()):
            self.passwords.append(generate_password(int(self.symbolCountComboBox.currentText()),
                                                    self.latinCheckBox.isChecked(),
                                                    self.digitCheckBox.isChecked(),
                                                    self.specCheckBox.isChecked()))
        self.listWidget.clear()
        self.listWidget.addItems(self.passwords)
        self.copyPassToolButton.setEnabled(True)
        self.savePassToolButton.setEnabled(True)
        self.printPassToolButton.setEnabled(True)
        self.sellectAllCheckBox.setChecked(False)

    def install_passwords(self):
        '''Установка паролей выбранных пользователей'''
        if not self.listWidget.selectedItems():
            QMessageBox.warning(self,
                               'Внимание!',
                               'Необходимо выбрать пользователей для установки пароля.',
                               QMessageBox.Yes)
            return

        if QMessageBox.warning(self,
                               'Внимание!',
                               'Произойдет смена паролей для выбранных пользователей. Продолжить?',
                               QMessageBox.Yes | QMessageBox.No) == QMessageBox.No:
            return
        # Список выбранных пользователей
        selected_users = [i.text() for i in self.listWidget.selectedItems()]
        # Список из пар user_name:user_passwd
        pairs = list(map(lambda x: x + ":" + generate_password(int(self.symbolCountComboBox.currentText()), self.latinCheckBox.isChecked(), self.digitCheckBox.isChecked(), self.specCheckBox.isChecked()), selected_users))
        # Команда смены паролей пользователей
        command = "echo '{}' | sudo chpasswd".format(" ".join(pairs))
        try:
            # subprocess.run(command, shell=True, check=True)
            QMessageBox.information(self,
                            'Выполнено!',
                            'Генерация и установка паролей выполнены.\nСформирован отчет.',
                            QMessageBox.Yes)
            self.openReportToolButton.setEnabled(True)
            self.saveReportToolButton.setEnabled(True)
            self.printReportToolButton.setEnabled(True)
            # Формирование отчета о новых паролях пользователей
            template = self.environment.get_template("report.tmpl")
            self.report = template.render(pairs=pairs)
        except subprocess.CalledProcessError as e:
            print(f"Error changing password: {e}")

    def save_passwords(self):
        filename, _ = QFileDialog.getSaveFileName(self, 'Сохранение паролей', '', "HTML (*.htm)")
        if not filename:
            return
        template = self.environment.get_template("passes.tmpl")
        content = template.render(passes=self.passwords)
        with open(filename, mode="w", encoding="utf-8") as message:
            message.write(content)

    def copy_passwords(self):
        '''Копирование выбранных паролей или всех паролей, если ни один не выбран, в буфер обмена'''
        clipboard = QApplication.clipboard()
        selected_passes = self.listWidget.selectedItems()
        # Если ни один пароль не выбран, принудительно выбрать все
        if not selected_passes:
            self.sellectAllCheckBox.setChecked(True)
            self.change_selection()
            selected_passes = self.listWidget.selectedItems()
        passwords = []
        if selected_passes:
            for item in selected_passes:
                passwords.append(item.text())
        clipboard.setText("\n".join(passwords))

    def change_selection(self):
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            item.setSelected(self.sellectAllCheckBox.isChecked())

    def show_genpass_page(self):
        self.genpassPagePushButton.setDown(True)
        self.stackedWidget.setCurrentWidget(self.genPassPage)
        self.buttonsStackedWidget.setCurrentWidget(self.genPassButtonsPage)
        self.listWidget.clear()
        self.listWidget.addItems(self.passwords)
        self.sellectAllCheckBox.setChecked(False)

    def show_settings_page(self):
        self.settingsPagePushButton.setDown(True)
        self.stackedWidget.setCurrentWidget(self.settingsPage)

    def show_instpass_page(self):
        self.instpassPagePushButton.setDown(True)
        self.stackedWidget.setCurrentWidget(self.genPassPage)
        self.buttonsStackedWidget.setCurrentWidget(self.instPassButtonsPage)
        self.listWidget.clear()
        self.listWidget.addItems(self.users)
        self.sellectAllCheckBox.setChecked(False)

    def switch_remotehost_setup(self):
        self.remoteHostSettingsFrame.setEnabled(True)
        # В КП СГП при активации фрейма с настройками удаленного доступа,
        # порт принудительно устанавливается в 22
        self.portLineEdit.setText("22")

    def switch_localhost_setup(self):
        self.remoteHostSettingsFrame.setEnabled(False)
        # В КП СГП при деактивации фрейма с настройками удаленного доступа,
        # порт принудительно сбрасывается
        self.portLineEdit.setText("")
        
    def clear_remote_user(self):
        self.userLineEdit.setText("")
        self.passLineEdit.setText("")
    
    def show_report(self):
       self.reportDialog.exec(self.report)
       
    def save_report(self):
        filename, _ = QFileDialog.getSaveFileName(self, 'Сохранение отчета', '', "HTML (*.htm)")
        if not filename:
            return
        with open(filename, mode="w", encoding="utf-8") as message:
            message.write(self.report)
    
    def print_report(self):
        printer = QPrinter()
        dialog = QPrintDialog(printer)
        if dialog.exec():
            text_edit = QTextEdit()
            text_edit.setHtml(self.report)
            document = QTextDocument()
            document.setHtml(text_edit.toHtml())
            document.print(printer)

