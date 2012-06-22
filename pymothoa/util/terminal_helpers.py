HEADER = '\033[95m'
FAIL = '\033[91m'
CLOSE = '\033[0m'

def header(S): return HEADER + S + CLOSE

def fail(S): return FAIL + S + CLOSE
