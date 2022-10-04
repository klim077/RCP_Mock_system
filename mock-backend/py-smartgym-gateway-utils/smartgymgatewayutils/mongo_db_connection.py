

class MDB:
    def __init__(self, ip: str, port: int, username: str, password: str):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password

    def __enter__(self):
        from pymongo import MongoClient
        self.client = MongoClient(
            self.ip, self.port, username=self.username, password=self.password)
        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        del self.client