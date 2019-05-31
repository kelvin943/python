import os
from pathlib import Path

if __name__ == "__main__":
    print (os.path.dirname(__file__))
    print (os.getcwd())

    print (Path.cwd())
