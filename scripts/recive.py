import socket
import json
import threading

class SimpleOsuTcpReceiver:
    """极简版 osu! TCP JSON 接收器（类封装）"""
    
    def __init__(self, host="127.0.0.1", port=64574):
        self.host = host  # 监听地址
        self.port = port  # 监听端口（与C#端一致）
        self.is_running = False  # 运行状态
        self.server_socket = None  # 服务器套接字
        self.client_socket = None  # 客户端套接字
        self.receive_thread = None  # 接收线程

    def start(self):
        """启动接收器"""
        if self.is_running:
            print("接收器已在运行！")
            return
        
        self.is_running = True
        # 创建TCP套接字
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            print(f"接收器启动成功！监听 {self.host}:{self.port}")
            print("等待 osu! 客户端连接...")
            
            # 启动接收线程（异步处理，不阻塞主线程）
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
        except Exception as e:
            print(f"启动失败：{e}")
            self.stop()

    def stop(self):
        """停止接收器"""
        self.is_running = False
        
        # 关闭客户端连接
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        
        # 关闭服务器套接字
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        print("\n接收器已停止")

    def _receive_loop(self):
        """接收循环（运行在子线程）"""
        buffer = b""  # 缓存不完整数据包（处理粘包）
        
        while self.is_running:
            # 等待客户端连接
            if not self.client_socket:
                try:
                    self.server_socket.settimeout(1.0)
                    self.client_socket, addr = self.server_socket.accept()
                    print(f"客户端连接成功：{addr}")
                    print("开始接收数据（按 Ctrl+C 停止）\n")
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"连接失败：{e}")
                    break
            
            # 接收并处理数据
            try:
                self.client_socket.settimeout(1.0)
                data = self.client_socket.recv(4096)  # 一次接收4KB数据
                
                if not data:  # 客户端断开
                    print("客户端已断开连接，等待重新连接...")
                    self.client_socket = None
                    buffer = b""
                    continue
                
                # 按换行符分割数据（与C#端 \n 分隔符对应）
                buffer += data
                while b"\n" in buffer:
                    line_bytes, buffer = buffer.split(b"\n", 1)
                    if not line_bytes:
                        continue
                    
                    # 解析JSON并打印
                    try:
                        json_str = line_bytes.decode("utf-8").strip()
                        data_dict = json.loads(json_str)
                        print("接收到JSON数据：", data_dict)
                    except json.JSONDecodeError:
                        print(f"警告：无效JSON - {line_bytes}")
                    except Exception as e:
                        print(f"处理数据失败：{e}")
            
            except socket.timeout:
                continue
            except Exception as e:
                print(f"接收数据异常：{e}")
                self.client_socket = None
                buffer = b""

# 测试主函数
if __name__ == "__main__":
    # 创建接收器实例
    receiver = SimpleOsuTcpReceiver(host="0.0.0.0", port=64574)
    
    try:
        # 启动接收器
        receiver.start()
        # 主线程阻塞（按 Ctrl+C 退出）
        while receiver.is_running:
            input()
    except KeyboardInterrupt:
        # 捕获 Ctrl+C 信号，优雅停止
        receiver.stop()