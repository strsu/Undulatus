import socket
import threading
import time
import os

class receive(threading.Thread):
    def __init__(self, client_socket, name, room):
        super().__init__()
        self.client_socket = client_socket
        self.name = name
        self.room = room
        self.size = 102400
        self.user_name = os.path.expanduser('~')

    def run(self):
        while True:
            data = self.client_socket.recv(self.size)
            
            if data:
                msg = data.decode().split(':')
                name = msg[0]
                msg = msg[1]

                if msg == 'send':
                    data = self.client_socket.recv(self.size)
                    fname, fsize = data.decode().split(':')[1:]
                    file = open(os.path.join(f'{self.user_name}\\Downloads', fname), 'wb')
                    fsize = int(fsize)
                    data = self.client_socket.recv(self.size)
                    rev_size = len(data)

                    while data:
                        file.write(data)
                        data = self.client_socket.recv(self.size)
                        if data == b'Done':
                            file.close()
                            break
                        rev_size += len(data)
                        x = int(rev_size*100/fsize)
                        print(f'{x}%', '*'*x, end='\r')

                    print('\nDone Receiving', msg)

                else:
                    print(name, ':', msg, end='\n>> ')

class myChat(threading.Thread):
    def __init__(self, client_socket, name, room):
        super().__init__()
        self.client_socket = client_socket
        self.name = name
        self.room = room
        self.size = 102400 # 초당 약 2mb의 속도를 보인다.

    def run(self):
        while True:
            print('>> ', end='')
            msg = input()
            
            if msg is not None:
                self.client_socket.sendall((self.name+':'+msg).encode())
                
                #print(msg[0],':', repr(data.decode()))
    
            if msg == 'q':
                break

            if msg == 'send':
                print('path:', end=' ')
                fpath = input()
                print('name:', end=' ')
                fname = input()
                
                if not os.path.exists(os.path.join(fpath, fname)):
                    print("No Such File or Directory, Please Check!")
                    continue
                
                data = open(os.path.join(fpath, fname), 'rb')
                fsize = str(os.path.getsize(os.path.join(fpath, fname)))
                self.client_socket.sendall((self.name+':'+fname+':'+fsize).encode())
                
                # 파일을 전부 다 읽는데는 시간이 오래 걸린다.
                # 때문에 보낼 크기를 지정해서 해당 사이즈 만큼 읽고 보내는 방식을 반복해야
                # 큰 파일도 빠르게 보낼 수 있다.
                # 즉, 파일 전체를 보내게 되면 읽는데 10분이 걸린다 했을 때 10분간의 지연시간이 생긴다.
                # 때문에 특정 크기씩 읽어가면서 파일을 보내는 것이 더 빠르다.
                prev_tell = 0
                self.client_socket.sendall(data.read(self.size))
                while prev_tell != data.tell():
                    prev_tell = data.tell()
                    try:
                        self.client_socket.sendall(data.read(self.size))
                    except Exception as e:
                        print(e)
                    
                print('Done sending')
                self.client_socket.sendall(('Done').encode())
                data.close()

            msg = None

Host = '127.0.0.1' # 연결할 서버의 외부 IP 주소
Port = 9999        # 연결할 서버의 포트번호

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((Host, Port))

msg = None
print('name>> ', end='')
name = input()
print('room>> ', end='')
room = input()

t1 = myChat(client_socket, name, room)
t2 = receive(client_socket, name, room)

t1.start()
t2.start()

while True:
    # 일단은 두 쓰레드 중 하나라도 죽으면 프로그램 종료.
    if not t1.is_alive() or not t2.is_alive():
        try:
            client_socket.close()
        except Exception as e:
            print(e)
        finally:
            break
