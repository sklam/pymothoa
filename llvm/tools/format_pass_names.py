with open('OPT_O3_PASSES') as fin:
    items = fin.read()
    for line in filter(bool, items.split(' ')):
        short = line.strip().lstrip('-')
        print short

