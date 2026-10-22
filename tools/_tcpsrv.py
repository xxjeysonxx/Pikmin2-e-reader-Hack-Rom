import socket
s=socket.socket(); s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
s.bind(('127.0.0.1',2399)); s.listen(1)
print('listening',flush=True)
c,a=s.accept(); print('conn',a,flush=True); c.send(b'hola'); c.close()
