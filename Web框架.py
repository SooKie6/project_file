import socket
import sys
import threading
import framework
import logging


logging.basicConfig(Level=logging.DEBUG,
                    format='%(asctime)s - %(filename)s [line: %(lineno)d] - %(levelname)s: %(message)s',
                    filename='log.txt',
                    filemode='a'
                    )


class HttpWebServer(object):
    def __init__(self, port):
        top_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        top_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        top_server_socket.bind(('', port))
        top_server_socket.listen(128)

        self.top_server_socket = top_server_socket

    def start(self):
        while True:
            new_client, client_addr_info = self.top_server_socket.accept()
            print('客户端连接的是：', client_addr_info)
            # 创建新的线程服务客户端
            sub_thread = threading.Thread(target=self.hand_client, args=(new_client,))
            # 守护线程,主线程结束.子线程也结束
            sub_thread.setDaemon(True)
            sub_thread.start()

    @staticmethod
    def hand_client(new_client):
        # 接受浏览器请求报文
        recv_data = new_client.recv(1024)
        if not recv_data:
            print('客户端下线的是：')
            new_client.close()
            return
        content_data = recv_data.decode('utf-8')
        data_list = content_data.split(' ', maxsplit=2)
        file_path = data_list[1]
        print(data_list)
        if file_path == '/':
            file_path = '/index.html'

        # 根据请求后缀判断什么请求
        if file_path.endswith('.html'):
            logging.info('动态资源请求:' + file_path)
            # 建立请求资源的字典
            env = {
                'request_path': file_path
                # 其他请求信息，可以在字典后添加
            }
            status, head, response_body = framework.handle_request(env)
            response_line = 'Http/1.1 %s\r\n' % status
            response_heads = ''
            for heads in head:
                response_heads += '%s: %s\r\n' % heads

            response_data = (response_line + response_heads + '\r\n' + response_body).encode('utf-8')
            # 发送Http响应报文给浏览器
            new_client.send(response_data)
            new_client.close()
        else:
            # 静态资源请求
            logging.info('静态资源请求:' + file_path)
            try:
                with open('static' + file_path, 'rb') as file:
                    file_data = file.read()
            except Exception:
                response_line = 'http/1.1 404 Not Found\r\n'
                response_head = 'Server: SQW/1.1\r\n'
                with open('static' + '/error.html', 'rb') as f:
                    error_data = f.read()
                response_body = error_data
                # 拼接响应报文
                response_data = (response_line + response_head + '\r\n').encode('utf-8') + response_body
            else:
                response_line = 'http/1.1 200 OK\r\n'
                response_head = 'Server: SQW/1.1\r\n'
                response_body = file_data
                response_data = (response_line + response_head + '\r\n').encode('utf-8') + response_body
            new_client.send(response_data)
            new_client.close()


def main():
    # 判断参数是否两个，如果不是提示用法
    if len(sys.argv) != 2:
        print('用法： python3 xxx.py 端口号')
        logging.warning('启动程序的参数必须是两个')
        return
    # 判断第二个参数是不是数字，如果不是，提示用法
    if not sys.argv[1].isdigit():
        print('用法： python3 xxx.py 端口号')
        logging.warning('启动程序的参数,必须是数字字符串')
        return

    # 转换字符串为int
    port = int(sys.argv[1])
    web_server = HttpWebServer(port)
    web_server.start()


if __name__ == '__main__':
    main()