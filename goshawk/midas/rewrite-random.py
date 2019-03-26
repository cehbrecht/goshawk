import re, sys, os
import random


def rewrite_csv(csv, random_cols=[2, 8, 9]):
    with open(csv) as reader:
        data = reader.readlines()

    cols = []

    for count, line in enumerate(data):
        line = line.strip()
        items = re.split(", ", line)
        n = len(items)
        assert(", ".join(items) == line) 

        if not cols:
            cols = [[] for i in items]

        for i, value in enumerate(items):
            cols[i].append(value)

    for col in random_cols:
        _copy = cols[col][:]
        random.shuffle(_copy)
        cols[col] = _copy

    new_file = csv.replace('midas', 'nonsense-data')

    with open(new_file, 'w') as writer:
        
        for i in range(count):
            line = ", ".join([cols[_][i] for _ in range(n)]) + "\n"
            writer.write(line)
    
    print('Wrote: {0}'.format(new_file))


if __name__ == '__main__':

    for arg in sys.argv[1:]:
        rewrite_csv(arg)

        
