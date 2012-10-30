import random
from time import *

def rand_matrix(dim):
    # Create random MxM matrix
    new_matrix = [[random.random() for row in range(dim)] for col in range(dim)]
    return new_matrix

def mult(matrix1,matrix2):
    # Matrix multiplication
    if len(matrix1[0]) != len(matrix2):
        # Check matrix dimensions
        print 'Matrices must be m*n and n*p to multiply!'
    else:
        # Multiply if correct dimensions (don't save results)
        for i in range(len(matrix1)):
            for j in range(len(matrix2[0])):
                elem = 0
                for k in range(len(matrix2)):
                    elem += matrix1[i][k]*matrix2[k][j]

def time_mult(matrix1,matrix2):
    # Clock the time matrix multiplication takes
    start = clock()
    new_matrix = mult(matrix1,matrix2)
    end = clock()

    fmtString = "%dx%d matrix multiplication has completed successfully and took %.2f seconds."
    vals = (len(matrix1[0]),len(matrix1[0]),end-start)

    return fmtString % vals

def compute(dim):
    a = rand_matrix(dim)
    b = rand_matrix(dim)
    return time_mult(a,b)
