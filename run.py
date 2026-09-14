import socket
import uvicorn

def local_ip():
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect(("8.8.8.8",80)); ip=s.getsockname()[0]; s.close(); return ip
    except Exception:
        try: return socket.gethostbyname(socket.gethostname())
        except Exception: return "127.0.0.1"

if __name__ == "__main__":
    ip=local_ip()
    print("\n"+"="*68)
    print(" ELECCIONES ESCOLARES - I.E. FRANCISCO BOLOGNESI CERVANTES")
    print("="*68)
    print(" En esta laptop:       http://127.0.0.1:8000")
    print(f" En otras laptops:     http://{ip}:8000")
    print(" Panel administrador:  /admin/login")
    print(" Contraseña inicial:   FBC2026!   (CAMBIAR EN EL PRIMER INGRESO)")
    print("="*68+"\n")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
