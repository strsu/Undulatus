import socket
import threading
from queue import Queue
import time
import os
import cv2

class Receiver(threading.Thread):
    def __init__(self, msgQ, client_socket, addr):
        super().__init__()
        self.msgQ = msgQ
        self.client_socket = client_socket
        self.addr = addr
        self.size = 102400
        self.user_name = os.path.expanduser('~')

    def run(self):
        print('Receiver start -', self.addr)
        while True:
            try:
                data = self.client_socket.recv(self.size)
                if data:
                    msg = data.decode().split(':')
                    name = msg[0]
                    msg = msg[1]
                    print(name, ':', msg)
                    self.msgQ.put([self.client_socket, data])

                    if msg == 'send':
                        data = self.client_socket.recv(self.size)
                        self.msgQ.put([self.client_socket, data])

                        fname, fsize = data.decode().split(':')[1:]
                        
                        fsize = int(fsize)
                        file = open(os.path.join(f'{ self.user_name}\\Downloads', fname), 'wb')
                        data = self.client_socket.recv(self.size)
                        rev_size = len(data)
                        print(time.strftime('%c', time.localtime(time.time())))
                        while data:
                            file.write(data)
                            self.msgQ.put([self.client_socket, data])
                            data = self.client_socket.recv(self.size)
                            if data == b'Done':
                                file.close()
                                self.msgQ.put([self.client_socket, b'Done'])
                                break
                            rev_size += len(data)
                            x = int(rev_size*100/fsize)
                            print(f'{x}%', '*'*x, end='\r')

                        print('Done Receiving', msg)
                        print(time.strftime('%c', time.localtime(time.time())))
                        file.close()
            except Exception as e: # ???????????? ??????
                # ???????????? ?????????, ????????? ???????????? ????????? ?????? ??????
                # ??? ????????? ????????? ??????????????? ?????? ?????? ????????? ??????????????????.
                client_socket_queue.put((self.client_socket, self.addr))
                return True

class Sender(threading.Thread):
    def __init__(self, clientQ, msgQ):
        super().__init__()
        self.clientQ = clientQ
        self.msgQ = msgQ

        self.client = {}

    def run(self):
        while True:
            if self.clientQ.qsize() > 0:
                client_socket, addr = self.clientQ.get()
                if client_socket in self.client:
                    del self.client[client_socket]
                else:
                    self.client[client_socket] = addr
            
            if self.msgQ.qsize() > 0:
                client, data = self.msgQ.get()
                for key, val in self.client.items():
                    if key == client:
                        continue
                    try:
                        key.sendall(data)
                    except Exception as e:
                        print(e, val)

if __name__ == "__main__":

    Host = '0.0.0.0' # ????????? 0.0.0.0?????? ?????????
    Port = 9999      # ????????? ??????

    # ?????? ????????? ??????
    # ?????? ?????? IPv4, TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # ?????? ??????????????? ????????? ??? ?????????
    # WinError 10048 ?????? ????????? ?????? ??????
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # bind ????????? ????????? ?????? ???????????? ?????????????????? ?????? ????????? ??????????????? ??????
    server_socket.bind((Host, Port))

    # ????????? ?????????????????? ????????? ???????????????
    server_socket.listen()

    client_socket_queue = Queue()
    client_data_queue = Queue()

    #sender = threading.Thread(target=Sender, args=(client_socket_queue, client_data_queue))
    sender = Sender(client_socket_queue, client_data_queue)
    sender.start()

    receiver = []

    while True:

        # accept ???????????? ??????????????? ?????????????????? ???????????? ????????? ????????? ??????
        client_socket, addr = server_socket.accept()
        client_socket_queue.put((client_socket, addr))

        receiver_ = Receiver(client_data_queue, client_socket, addr)
        receiver_.start()
        receiver.append(receiver_)

        print('new client access', addr, client_socket_queue)


    client_socket.close()
    server_socket.close()
