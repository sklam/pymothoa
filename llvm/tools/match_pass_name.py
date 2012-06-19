with open('PASSES') as fin:
    source = fin.readlines()

with open('PASS_SHORT') as fin:
    for line in fin:
        short = line.strip()
        for line in source:
            if line.startswith(short):
                print line
                break
        else:
            print short, '?'*10

