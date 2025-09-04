import sys
import importlib

def test_imports():
    required_modules = [
        'requests',
        'bs4',
        'lxml',
        'fake_useragent',
        'stem'
    ]
    
    print("Testing imports...")
    failed = []
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            failed.append(module)
    
    return failed

def test_tor():
    try:
        import requests
        import socks
        import socket
        
        print("Testing Tor...")
        
        socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
        socket.socket = socks.socksocket
        
        response = requests.get("http://httpbin.org/ip", timeout=10)
        print(f"✓ Tor working. IP: {response.json()['origin']}")
        
        socket.socket = socket._socketobject
        return True
        
    except Exception as e:
        print(f"✗ Tor failed: {e}")
        return False

def test_scraper():
    try:
        print("Testing scraper...")
        from scraper import DarkWebScraper
        
        scraper = DarkWebScraper()
        print("✓ Scraper class works")
        return True
        
    except Exception as e:
        print(f"✗ Scraper failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Installation Test ===\n")
    
    failed_imports = test_imports()
    tor_working = test_tor()
    scraper_working = test_scraper()
    
    print("\n=== Results ===")
    
    if not failed_imports and tor_working and scraper_working:
        print("✅ All tests passed!")
        print("Run: python scraper.py")
    else:
        print("❌ Some tests failed")
        if not tor_working:
            print("  - Install and start Tor")
        if not scraper_working:
            print("  - Check scraper.py")
