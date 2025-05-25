import logging
from socket import AF_INET, SOCK_STREAM, socket
import threading

# 设置日志配置
logging.basicConfig(
    filename='server.log',  # 日志文件
    level=logging.INFO,  # 日志级别
    format='%(asctime)s - %(levelname)s - %(message)s',  # 日志格式
)

# 定义服务器端口
serverPort = 2525
# 创建 TCP 套接字
serverSocket = socket(AF_INET, SOCK_STREAM)
# 绑定套接字到地址和端口
serverSocket.bind(('', serverPort))
# 开始监听传入的连接
serverSocket.listen(5)
print('The server is ready to receive')


# 从文件读取用户数据
def load_users(filename):
    users = {}
    filename = "information.xls"
    with open(filename, 'r') as file:
        for line in file:
            userid, password, balance = line.strip().split(',')
            users[userid] = {'password': password, 'balance': float(balance)}
    return users

# 将用户数据写入文件
def save_users(filename, users):
    try:
        with open(filename, 'w') as file:
            for userid, data in users.items():
                file.write(f"{userid},{data['password']},{data['balance']}\n")
    except Exception as e:
        logging.error(f"Error saving user data to {filename}: {e}")


# 处理客户端请求的函数
def handle_client(connectionSocket, addr, users):
    logging.info(f"Connection from {addr} has been established!")

    try:
        # HELO <userid>
        userid = connectionSocket.recv(1024).decode().strip()
        if userid not in users:
            connectionSocket.send("User ID not found!".encode())
            logging.warning(f"User ID '{userid}' not found for address {addr}.")
            connectionSocket.close()
            return

        connectionSocket.send("500 sp AUTH REQUIRED!".encode())

        # PASS <password>
        password = connectionSocket.recv(1024).decode().strip()
        if users[userid]['password'] != password:
            connectionSocket.send("525 ERROR! (password is NOT OK)".encode())
            logging.warning(f"Invalid password attempt for user '{userid}' from address {addr}.")
            connectionSocket.close()
            return

        connectionSocket.send("525 OK! (password is OK)".encode())

        # 持续处理请求
        while True:
            request = connectionSocket.recv(1024).decode().strip()
            if request == "bye":
                connectionSocket.send("Connection closed.".encode())
                break  # 退出循环
            elif request == "balance":
                # 发送余额给客户端
                connectionSocket.send(f"AMNT:{users[userid]['balance']}".encode())
            elif request.startswith("withdraw"):
                # 处理取款逻辑
                try:
                    amount_str = request.split()[1]
                    amount = float(amount_str)
                    if amount <= users[userid]['balance']:
                        users[userid]['balance'] -= amount
                        connectionSocket.send("525 OK (ATM dispenses)".encode())
                        logging.info(
                            f"{amount} withdrawn from user '{userid}'. New balance: {users[userid]['balance']}.")
                        save_users('information.txt', users)
                    else:
                        connectionSocket.send("401 sp ERROR! (not enough balance)".encode())
                        logging.warning(f"Insufficient balance for user '{userid}' withdrawal attempt of {amount}.")
                except (ValueError, IndexError):
                    connectionSocket.send("Invalid withdraw request format".encode())
                    logging.error(f"Invalid withdraw request format from user '{userid}': {request}.")
            else:
                connectionSocket.send("Unknown command".encode())
                logging.warning(f"Unknown command received from user '{userid}': {request}.")

    except Exception as e:
        logging.error(f"Error handling client {addr}: {e}")
    finally:
        connectionSocket.close()
        logging.info(f"Connection with {addr} closed.")


# 主循环，等待并处理客户端连接
users = load_users('users.txt')  # 加载用户数据
while True:
    try:
        # 接受一个传入的连接
        connectionSocket, addr = serverSocket.accept()
        # 创建一个新线程来处理该客户端请求
        client_thread = threading.Thread(target=handle_client, args=(connectionSocket, addr, users))
        client_thread.start()
    except KeyboardInterrupt:
        print("Server is shutting down.")
        break
    except Exception as e:
        logging.error(f"Error accepting connections: {e}")

# 关闭服务器套接字
serverSocket.close()