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
            with open(self.tempstore, "r") as f:
                self.options = json.load(f)

    def __getitem__(self,index):
        return self.options[index]

    def __setitem__(self, key, val):
        self.options[key] = val
        self.store()

    def __contains__(self, item):
        return (item in self.options.keys())

    def __iter__(self):
        return list.__iter__(self.options.keys())

    def pop(self, key, default=None):
        return self.options.pop(key, default)


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
