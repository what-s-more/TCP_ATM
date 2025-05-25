import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QDialog, QFormLayout, QLineEdit, QDialogButtonBox
from PyQt5.QtGui import QIntValidator
from socket import *

serverName = '172.28.64.1'
serverPort = 2525
clientSocket = socket(AF_INET, SOCK_STREAM)

try:
    clientSocket.connect((serverName, serverPort))
except ConnectionRefusedError:
    print("无法连接到服务器，请检查服务器是否启动。")
    sys.exit(1)


class PasswordDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QFormLayout()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        # 限制输入为 6 位数字
        self.password_input.setValidator(QIntValidator(0, 999999))
        self.password_input.textChanged.connect(self.check_password_length)
        layout.addRow('密码:', self.password_input)
        self.setLayout(layout)
        self.setWindowTitle('插卡操作')

    def check_password_length(self, text):
        if len(text) == 6:
            self.accept()


class WithdrawDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QFormLayout()
        self.amount_input = QLineEdit()
        self.amount_input.setValidator(QIntValidator(1, 1000000))
        layout.addRow('取款金额:', self.amount_input)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
        self.setLayout(layout)
        self.setWindowTitle('取款')


class ATMClient(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # 创建主布局
        main_layout = QVBoxLayout()

        # 创建提示窗口
        self.prompt_label = QLabel("欢迎使用 ATM 客户端，请选择操作。")
        main_layout.addWidget(self.prompt_label)

        # 创建信息显示框
        self.info_display = QTextEdit()
        self.info_display.setReadOnly(True)
        main_layout.addWidget(self.info_display)

        # 创建按钮布局
        button_layout = QHBoxLayout()

        # 创建插卡按钮
        insert_card_button = QPushButton("插卡")
        insert_card_button.clicked.connect(self.insert_card)
        button_layout.addWidget(insert_card_button)

        # 创建退卡按钮
        eject_card_button = QPushButton("退卡")
        eject_card_button.clicked.connect(self.eject_card)
        button_layout.addWidget(eject_card_button)

        # 创建取款按钮
        withdraw_button = QPushButton("取款")
        withdraw_button.clicked.connect(self.withdraw)
        button_layout.addWidget(withdraw_button)

        # 创建查询按钮
        query_button = QPushButton("查询余额")
        query_button.clicked.connect(self.query)
        button_layout.addWidget(query_button)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
        self.setWindowTitle('ATM 客户端')
        self.show()

    def insert_card(self):
        cardid = '666'
        clientSocket.send(cardid.encode('UTF-8'))
        recv_data = clientSocket.recv(1024).decode('UTF-8')
        self.info_display.append(f"服务端回复的消息是：{recv_data}")
        dialog = PasswordDialog()
        if dialog.exec_():
            password = dialog.password_input.text()
            try:
                send_msg = password
                clientSocket.send(send_msg.encode('UTF-8'))
                recv_data = clientSocket.recv(1024).decode('UTF-8')
                self.info_display.append(f"服务端回复的消息是：{recv_data}")
            except Exception as e:
                self.info_display.append(f"发生错误：{e}")

    def eject_card(self):
        try:
            send_msg = "bye"
            clientSocket.send(send_msg.encode('UTF-8'))
            recv_data = clientSocket.recv(1024).decode('UTF-8')
            self.info_display.append(f"服务端回复的消息是：{recv_data}")
            clientSocket.close()
            sys.exit(0)
        except Exception as e:
            self.info_display.append(f"发生错误：{e}")

    def withdraw(self):
        dialog = WithdrawDialog()
        if dialog.exec_():
            amount = dialog.amount_input.text()
            try:
                send_msg = f"withdraw {amount}"
                clientSocket.send(send_msg.encode('UTF-8'))
                recv_data = clientSocket.recv(1024).decode('UTF-8')
                self.info_display.append(f"取款后余额：{recv_data}")
            except Exception as e:
                self.info_display.append(f"发生错误：{e}")

    def query(self):
        try:
            send_msg = "balance"
            clientSocket.send(send_msg.encode('UTF-8'))
            recv_data = clientSocket.recv(1024).decode('UTF-8')
            self.info_display.append(f"当前余额：{recv_data}")
        except Exception as e:
            self.info_display.append(f"发生错误：{e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    atm_client = ATMClient()
    sys.exit(app.exec_())