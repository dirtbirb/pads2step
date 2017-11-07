class tester(object):

    def __init__(self, lister):
        self.one = next(lister)
        self.two = next(lister)
        self.three  = next(lister)

x = tester(iter([1, 2, 3]))

print(x.one, x.two, x.three)
