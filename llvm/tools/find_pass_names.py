import re
import os.path

PATH = '/home/michael/installed/llvm-3.1/llvm-3.1'

pattern = re.compile(r'INITIALIZE_PASS\s*\(\s*([a-zA-Z0-9]+)\s*,\s*"([^"]+)"', re.MULTILINE)

def listFiles(dir_path, extensions):
    fileList = []
    for root, subFolders, files in os.walk(dir_path):
        for file in files:
            ext = file.rsplit('.', 1)[-1]
            if ext in extensions:
                f = os.path.join(root, file)
                yield f

def main():
    for filepath in listFiles(PATH, set(['cpp', 'hpp', 'h', 'c'])):
        with open(filepath) as fin:
            content = fin.read()
            matches = pattern.findall(content)
            if matches:
                path = filepath[len(PATH):]
                print path.center(80, '-')
                for full, short in matches:
                    print '%s\t%s'%(short, full)

if __name__ == '__main__':
    main()
