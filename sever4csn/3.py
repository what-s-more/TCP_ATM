import socket
import tkinter as tk
from tkinter import ttk, messagebox

# 服务器配置
SERVER_IP = '127.0.0.1'  # 本地测试IP，确保与服务器一致
SERVER_PORT = 2525


class ATMClient:
    def __init__(self, root):
        self.root = root
        self.root.title("ATM终端")
        self.root.geometry("400x300")
        self.current_account = None
        self.sock = None
        self.setup_login_ui()
        self.connect_to_server()  # 连接服务器

    def connect_to_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((SERVER_IP, SERVER_PORT))
            print(f"成功连接到服务器 {SERVER_IP}:{SERVER_PORT}")
        except Exception as e:
            messagebox.showerror("连接失败", f"无法连接到服务器: {str(e)}")
            self.root.destroy()

    def setup_login_ui(self):
        self.clear_ui()
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        ttk.Label(main_frame, text="欢迎使用，请登录！", font=('微软雅黑', 12, 'bold')).pack(pady=10)
        form_frame = ttk.Frame(main_frame)
        form_frame.place(relx=0.5, rely=0.5, anchor='center')

        ttk.Label(form_frame, text="账号：").grid(row=0, column=0, pady=5, sticky='e')
        self.acc_entry = ttk.Entry(form_frame, width=20)
        self.acc_entry.grid(row=0, column=1, pady=5, padx=5)

        ttk.Label(form_frame, text="密码：").grid(row=1, column=0, pady=5, sticky='e')
        self.pwd_entry = ttk.Entry(form_frame, show="*", width=20)
        self.pwd_entry.grid(row=1, column=1, pady=5, padx=5)

        ttk.Button(form_frame, text="登 录", command=self.login, width=15).grid(row=2, columnspan=2, pady=15)

    def setup_main_ui(self):
        self.clear_ui()
        main_frame = ttk.Frame(self.root)
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        ttk.Label(main_frame, text=f"欢迎您：用户{self.current_account}", font=('微软雅黑', 12, 'bold')).pack(pady=10)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.place(relx=0.5, rely=0.5, anchor='center')

        ttk.Button(btn_frame, text="查询余额", width=12, command=self.check_balance).grid(row=0, column=0, padx=5,
                                                                                          pady=5)
        ttk.Button(btn_frame, text="取  款", width=12, command=lambda: self.show_amount_dialog('withdraw')).grid(row=0,
                                                                                                                 column=1,
                                                                                                                 padx=5,
                                                                                                                 pady=5)
        ttk.Button(btn_frame, text="存  款", width=12, command=lambda: self.show_amount_dialog('deposit')).grid(row=1,
                                                                                                                column=0,
                                                                                                                padx=5,
                                                                                                                pady=5)
        ttk.Button(btn_frame, text="退  出", width=12, command=self.logout).grid(row=1, column=1, padx=5, pady=5)

        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, foreground="#666", padding=(10, 5),
                               anchor='center')
        status_bar.pack(side='bottom', fill='x')

    def clear_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def send_command(self, command):
        """发送命令并获取响应，增加调试日志"""
        try:
            print(f"发送命令: {command}")
            self.sock.send(command.encode('utf-8'))
            response = self.sock.recv(1024).decode('utf-8').strip()
            print(f"接收响应: {response}")
            return response
        except Exception as e:
            messagebox.showerror("通信错误", f"发送命令失败: {str(e)}")
            self.on_closing()
            return None

    def login(self):
        account = self.acc_entry.get().strip()
        password = self.pwd_entry.get().strip()

        if not account or not password:
            messagebox.showerror("错误", "账号和密码不能为空")
            return

        # 1. 发送HELO命令（格式：HELO <userid>）
        helo_cmd = f"{account}"  # 添加HELO前缀
        helo_response = self.send_command(helo_cmd)
        if not helo_response:
            return

        # 处理HELO响应
        if "User ID not found" in helo_response:
            messagebox.showerror("登录失败", helo_response)
            return
        elif "500 sp AUTH REQUIRED!" not in helo_response:
            messagebox.showerror("登录失败", f"未知响应: {helo_response}")
            return

        # 2. 发送PASS命令（格式：PASS <password>）
        pass_cmd = f"{password}"
        pass_response = self.send_command(pass_cmd)
        if not pass_response:
            return

        # 处理PASS响应 - 使用更精确的匹配
        if "525 OK! (password is OK)" in pass_response:
            self.current_account = account
            self.setup_main_ui()
            self.status_var.set("登录成功")
        elif "525 ERROR! (password is NOT OK)" in pass_response:
            messagebox.showerror("登录失败", "密码错误")
        else:
            messagebox.showerror("登录失败", f"认证失败: {pass_response}")

    def check_balance(self):
        # 发送balance命令
        balance_response = self.send_command("balance")
        if not balance_response:
            return

        # 解析余额（格式：AMNT:<金额>）
        if balance_response.startswith("AMNT:"):
            balance = balance_response.split(":")[1]
            messagebox.showinfo("账户余额", f"当前余额：{balance} 元")
            self.status_var.set("查询成功")
        else:
            messagebox.showerror("查询失败", balance_response or "无响应")

    def show_amount_dialog(self, action_type):
        # 金额输入对话框（优化错误处理）
        dialog = tk.Toplevel(self.root)
        dialog.title("输入金额" if action_type == 'deposit' else "取款金额")
        dialog.geometry("250x150")
        content_frame = ttk.Frame(dialog)
        content_frame.pack(expand=True, fill='both', padx=20, pady=20)

        ttk.Label(content_frame, text="请输入金额：").pack(pady=5)
        amount_entry = ttk.Entry(content_frame)
        amount_entry.pack(pady=5)

        def confirm():
            amount_str = amount_entry.get().strip()
            if not amount_str or not amount_str.replace('.', '', 1).isdigit():
                messagebox.showerror("输入错误", "请输入有效的数字金额！")
                return

            amount = float(amount_str)
            if amount <= 0:
                messagebox.showerror("输入错误", "金额必须大于0！")
                return

            # 构造命令（仅支持withdraw，服务器未实现deposit）
            if action_type == 'withdraw':
                cmd = f"withdraw {amount}"
                action_cn = "取款"
            else:
                messagebox.showerror("功能限制", "服务器暂不支持存款")
                dialog.destroy()
                return

            # 发送命令并处理响应
            response = self.send_command(cmd)
            if not response:
                dialog.destroy()
                return

            if "525 OK (ATM dispenses)" in response:
                # 成功后查询余额（需服务器支持返回新余额，当前需手动查询）
                self.check_balance()  # 调用查询余额更新显示
                self.status_var.set(f"{action_cn}成功")
            elif "401 sp ERROR! (not enough balance)" in response:
                messagebox.showerror("操作失败", "余额不足")
                self.status_var.set("余额不足")
            elif "Invalid withdraw request format" in response:
                messagebox.showerror("操作失败", "金额格式错误")
                self.status_var.set("金额格式错误")
            else:
                messagebox.showerror("操作失败", f"未知错误: {response}")
                self.status_var.set(f"错误: {response}")

            dialog.destroy()

        ttk.Button(content_frame, text="确  认", command=confirm).pack(pady=10)

    def logout(self):
        # 发送bye命令退出
        self.send_command("bye")
        self.current_account = None
        self.setup_login_ui()
        self.status_var.set("已安全退出账户")

    def on_closing(self):
        # 关闭前发送bye命令
        if self.sock:
            try:
                self.send_command("bye")
                self.sock.close()
            except:
                pass
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    client = ATMClient(root)
    root.protocol("WM_DELETE_WINDOW", client.on_closing)
    root.mainloop()