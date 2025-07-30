import jinja2
import logging
import os
import secrets
import string
import subprocess
from PyQt5 import uic
from PyQt5.Qt import QApplication, QDialog, QMessageBox, QFileDialog, QListWidget, QPrinter, QPrintDialog, QTextDocument, QTextEdit, QIntValidator, QRegExpValidator, QRegExp

from AboutDialog import AboutDialog
from ReportDialog import ReportDialog

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt='%Y-%m-%d %H:%M:%S')


def generate_password(length=8, require_letters=True, require_digits=True, require_punctuations=True):
    '''Сгенерировать пароль в соответствии с заданными в аргументах критериях сложности'''
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


def exec_command(command, host="localhost", port="22", user="admsec", passwd="123456"):
    '''Выполнить команду command локально или удаленно, в зависимости от параметра host'''
    users = []
    if host not in ("localhost", "127.0.0.1"):
        # Добавить к команде преамбулу для подключения к удаленному хосту
        command = "sshpass -p {} ssh {}@{} -p {} ".format(passwd, user, host, port) + command
    try:
        logging.info("Execute command: %s", command)
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE)
        logging.info("Get stdout: %s", result.stdout)
    except subprocess.CalledProcessError as e:
        logging.error(e)
        result = False
    return result


def change_passwords():
    pass


class MainDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(CURRENT_DIR, 'MainDialog.ui'), self)

        self.aboutDialog = AboutDialog()
        self.reportDialog = ReportDialog()

        self.environment = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(CURRENT_DIR), 'templates')))
        self.passwords = []
        self.users = []

        self.genpassPagePushButton.clicked.connect(self.show_genpass_page)
        self.settingsPagePushButton.clicked.connect(self.show_settings_page)
        self.instpassPagePushButton.clicked.connect(self.show_instpass_page)
        self.genPassPushButton.clicked.connect(self.generate_passwords)
        self.instPassPushButton.clicked.connect(self.install_passwords)
        self.savePassToolButton.clicked.connect(self.save_passwords)
        self.copyPassToolButton.clicked.connect(self.copy_passwords)
        self.printPassToolButton.clicked.connect(self.print_passwords)
        self.sellectAllCheckBox.clicked.connect(self.change_selection)
        self.aboutPushButton.clicked.connect(self.aboutDialog.exec)
        self.openReportToolButton.clicked.connect(self.show_report)
        self.saveReportToolButton.clicked.connect(self.save_report)
        self.printReportToolButton.clicked.connect(self.print_report)
        self.setRemotePassRadioButton.clicked.connect(self.toggle_host_setup)
        self.setLocalPassRadioButton.clicked.connect(self.toggle_host_setup)
        self.clearToolButton.clicked.connect(self.clear_remote_user)
        self.hostNameRadioButton.clicked.connect(self.set_hostname_validator)
        self.ipAddrRadioButton.clicked.connect(self.set_ipaddr_validator)

        self.listWidget.setSelectionMode(QListWidget.MultiSelection)

        # Несмотря на заданный диапазон, дает вводить любые пятизначные числа?!
        validator = QIntValidator(1, 65535)
        self.portLineEdit.setValidator(validator)
        # Установить валидатор имени хоста
        self.set_hostname_validator()
        # Требования POSIX к имени пользователя
        regexp = QRegExp('[A-Za-z0-9._][A-Za-z0-9._-]*')
        validator = QRegExpValidator(regexp)
        self.userLineEdit.setValidator(validator)

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
        # TODO Разобраться как быть, если sudo требует пароль, можно использовать -S для передачи пароля из stdin,
        # но stdin уже используется для передачи параметров!
        if exec_command(command):
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

    def save_passwords(self):
        filename, _ = QFileDialog.getSaveFileName(self, 'Сохранение паролей', '', "HTML (*.htm)")
        if not filename:
            return
        template = self.environment.get_template("passes.tmpl")
        content = template.render(passes=self.passwords)
        with open(filename, mode="w", encoding="utf-8") as message:
            message.write(content)

    def print_passwords(self):
        printer = QPrinter()
        dialog = QPrintDialog(printer)
        if dialog.exec():
            template = self.environment.get_template("passes.tmpl")
            content = template.render(passes=self.passwords)
            text_edit = QTextEdit()
            text_edit.setHtml(content)
            document = QTextDocument()
            document.setHtml(text_edit.toHtml())
            document.print(printer)

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
        '''Показать страницу настроек'''
        if self.setRemotePassRadioButton.isChecked() and not all([self.hostLineEdit.text(),
                                                                  self.portLineEdit.text(),
                                                                  self.userLineEdit.text(),
                                                                  self.passLineEdit.text()]):
            QMessageBox.warning(self,
                                'Внимание!',
                                'Необходимо заполнить все поля в настройках соединения',
                                QMessageBox.Yes)
            return

        if self.setRemotePassRadioButton.isChecked():
            result = exec_command('getent passwd | grep -E "/bin/(ba)?sh" | cut -d":" -f1',
                                      self.hostLineEdit.text(),
                                      self.portLineEdit.text(),
                                      self.userLineEdit.text(),
                                      self.passLineEdit.text())
        else:
            result = exec_command('getent passwd | grep -E "/bin/(ba)?sh" | cut -d":" -f1')

        # Фильтр нужен, т.к. последним элементом в список добавляется пустая строка
        self.users = list(filter(None, result.stdout.decode().split("\n")))
        self.instpassPagePushButton.setDown(True)
        self.stackedWidget.setCurrentWidget(self.genPassPage)
        self.buttonsStackedWidget.setCurrentWidget(self.instPassButtonsPage)
        self.listWidget.clear()
        self.listWidget.addItems(self.users)
        self.sellectAllCheckBox.setChecked(False)

    def toggle_host_setup(self):
        '''Активировать/деактивировать настройки удаленного доступа'''
        # В КП СГП сомнительное решение, когда при деактивации настроек порт принудительно сбрасывается,
        # а при активации всегда установливается значение 22. Здесь по дефолту 22 и не сбрасывается!
        self.remoteHostSettingsFrame.setEnabled(self.setRemotePassRadioButton.isChecked())

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

    def set_hostname_validator(self):
        # Требования POSIX к имени хоста
        regexp = QRegExp('[A-Za-z0-9][A-Za-z0-9-]{0,62}')
        validator = QRegExpValidator(regexp)
        self.hostLineEdit.setValidator(validator)
        self.hostLineEdit.setText("")

    def set_ipaddr_validator(self):
        ip_range = "(?:[0-1]?[0-9]?[0-9]|2[0-4][0-9]|25[0-5])"
        regexp = QRegExp("^" + ip_range + "\\." + ip_range + "\\." + ip_range + "\\." + ip_range + "$")
        validator = QRegExpValidator(regexp)
        self.hostLineEdit.setValidator(validator)
        self.hostLineEdit.setText("")
