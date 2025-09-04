import subprocess
import sys
import platform

def install_tor():
    system = platform.system().lower()
    
    if system == "darwin":
        try:
            subprocess.run(["brew", "install", "tor"], check=True)
            return True
        except:
            print("Install Tor manually from https://www.torproject.org/")
            return False
    elif system == "linux":
        try:
            subprocess.run(["sudo", "apt", "update"], check=True)
            subprocess.run(["sudo", "apt", "install", "-y", "tor"], check=True)
            return True
        except:
            print("Install Tor manually from https://www.torproject.org/")
            return False
    else:
        print("Install Tor manually from https://www.torproject.org/")
        return False

def test_tor():
    try:
        import requests
        import socks
        import socket
        
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
        socket.socket = socks.socksocket
        
        response = requests.get("http://httpbin.org/ip", timeout=10)
        print(f"Tor working. IP: {response.json()['origin']}")
        
        socket.socket = socket._socketobject
        return True
    except Exception as e:
        print(f"Tor test failed: {e}")
        return False

if __name__ == "__main__":
    print("Installing Tor...")
    if install_tor():
        print("Testing Tor...")
        test_tor()
