
def find_leading_edge(a,threshold=1000):
    above_thresh = [ int(el>threshold) for el in a ]
    return above_thresh.index(1)


if __name__ == "__main__":
    a=  10*[0.]
    a.extend( 10*[ 2000. ] )

    print find_leading_edge(a)
