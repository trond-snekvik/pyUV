import hashlib
import binascii
import json
import os
from os import path, environ

class Session:

    def __init__(self, directory):
        self.directory = directory
        self.options = {}
        h = hashlib.new("SHA1")
        h.update(self.directory)
        self.tempstore = path.join(environ["TEMP"], binascii.hexlify(h.digest())[:16] + ".json")
        if path.exists(self.tempstore):
            print self.tempstore
            with open(self.tempstore, "r") as f:
                self.options = json.load(f)


    def set(self, key, value):
        self.options[key] = value
        self.store()

    def store(self):
        j = None
        if os.path.exists(self.tempstore):
            with open(self.tempstore, "r") as f:
                j = json.load(f)
        if j:
            j.update(self.options)
            with open(self.tempstore, "w") as f:
                json.dump(j, f)
        else:
            with open(self.tempstore, "w") as f:
                f.write(json.JSONEncoder().encode(self.options))
