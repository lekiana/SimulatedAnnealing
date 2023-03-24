import numpy as np
import math
import sys
import random
import readData
import xlsxwriter as excel_writer
from time import perf_counter


def accept(cost_new, cost_cur, temp):
    if cost_new < cost_cur:
        return True
    else:
        return np.random.rand() <= np.exp(-abs(cost_new - cost_cur) / temp)


def swap_2(path):
    while True:  # random selection of two cities (indices)
        v1 = int(np.floor(np.random.uniform(0, len(path))))
        v2 = int(np.floor(np.random.uniform(0, len(path))))
        if v1 != v2:
            break
    path[v1], path[v2] = path[v2], path[v1]
    return path


def swap_2_count(path_len):  # n! / 2! (n – 2)!
    return math.comb(path_len, 2)


def swap_arch(path):
    path = list(path)
    while True:  # random selection of two cities
        v1 = int(np.floor(np.random.uniform(0, len(path))))
        v2 = int(np.floor(np.random.uniform(0, len(path))))
        if v1 != v2:
            break
    v1, v2 = sorted([v1, v2])
    bow = path[v1:v2]
    bow.reverse()
    path[v1:v2] = bow
    return np.array(path)


def swap_arch_count(path_len):
    sum = (path_len - 1) * path_len
    for i in range(1, path_len):
        sum -= i
    return sum


def not_good_enough(cost_cur, cost_opt):
    return (abs(cost_cur - cost_opt) / cost_opt * 100) >= 35  # percentage error greater than 35%


def get_cost(path, dist_mat, size):
    dist = 0
    num_location = size
    for i in range(num_location-1):
        dist += dist_mat[path[i]][path[i + 1]]
    dist += dist_mat[path[0]][path[num_location - 1]]
    return dist


def find_closest(dist_matrix, path):
    city_cur = path[-1]  # last city on current path
    city_best = 0
    best_dist = sys.float_info.max
    for i in range(len(dist_matrix)):
        if i not in path and i != city_cur:
            dist = dist_matrix[city_cur][i]
            if dist < best_dist:
                city_best = i
                best_dist = dist
    path.append(city_best)
    return path


def greedy(dist_matrix, size, path):  # pass the list
    for j in range(len(dist_matrix)):
        path = find_closest(dist_matrix, path)
    dist = get_cost(path, dist_matrix, size)
    return np.array(path), dist


def simulated_annealing(file_name, cost_opt, start_time):
    data = readData.read_data(file_name)
    matrix = data[0]
    size = data[1]

    # PARAMETERS INITIALIZATION #
    L = round(0.3 * swap_2_count(size))  # different % size of neighborhood
    k = 10  # number of the current SA iteration

    path = list()
    path.append(random.randint(0, size-1))

    # INITIAL SOLUTION #
    path_start = greedy(matrix, size, path)

    path_cur = path_new = path_best = prev_best = path_start[0]
    cost_cur = cost_best = prev_best = path_start[1]

    # 2 METHODS FOR SELECTING THE START TEMPERATURE #
    #temp_max = temp = cost_cur * 0.1  # initial solution cost * coefficient
    temp_max = temp = 20  # stała

    # SIMULATED ANNEALING #
    while not_good_enough(cost_cur, cost_opt):
        # cur_time = perf_counter()
        # elapsed = cur_time - start_time
        # if elapsed >= 120:
        #     break
        #     print('t > t_min')
        if temp < 1:
            print('T < T_min')
            break

        for i in range(L):

            # 2 METHODS OF SELECTING A SOLUTION IN THE NEXT TO THE CURRENT SOLUTION #
            path_new = swap_2(path_new)  # 2-replacement
            #path_new = swap_arch(path_new)  # arc swap

            cost_new = get_cost(path_new, matrix, size)

            if accept(cost_new, cost_cur, temp):
                # We update the current path
                path_cur = path_new.copy()
                cost_cur = cost_new

                if cost_new < cost_best:
                    path_best = path_new.copy()
                    cost_best = cost_new
            else:
                path_new = path_cur.copy()

        # 2 COOLING METHODS #
        alpha = 0.85 + math.log(0.95 + k)  # Boltzmann
        #alpha1 = 1 / 0.999 ** k  # geometric

        temp = temp_max / alpha
        k += 1

        # CURRENT TEMPERATURE AND COST OF SOLUTION #
        print("Temperature: " + str(round(temp, 2)),
              " Distance: " + str(cost_best))
    return cost_best, path_best


def excel_write(wb, it, opt, file):
    worksheet = wb.add_worksheet(file)
    worksheet.write(0, 0, 'Nazwa instancji')
    worksheet.write(1, 0, file)
    worksheet.write(0, 2, 'Liczba powtórzeń')
    worksheet.write(1, 2, it)
    worksheet.write(0, 4, 'Wartość optymalna')
    worksheet.write(1, 4, opt)
    worksheet.write(3, 0, 'Czas wykonywania [s]:')
    worksheet.write(3, 2, 'Uzyskany koszt: ')
    worksheet.write(3, 4, 'Błąd [%]: ')
    return worksheet


def main():
    # READ CONFIGURATION FILE #
    config_data = readData.read_config()
    data_files = config_data[0]
    iterators = config_data[1]
    optimal_values = config_data[2]
    output_files = config_data[4]

    # CREATE OUTPUT FILE(S)#
    workbooks = list()
    for file in output_files:
        workbooks.append(excel_writer.Workbook(file))
    wb = workbooks[0]

    # SA #
    idx = 0
    for file in data_files:
        it = iterators[idx]  # number of iterations
        opt = optimal_values[idx]  # optimal path value

        # WRITE TO OUTPUT FILE #
        worksheet = excel_write(wb, it, opt, file)

        # SIMULATED ANNEALING #
        print('\nInstance name: ' + file)
        print('Number of iterations: ' + str(it))
        for i in range(it):
            print("\nIteration: " + str(i + 1))
            start = perf_counter()  # start of timing
            sa = simulated_annealing(file, opt, start)
            c, p = sa
            end = perf_counter()  # end of timing
            elapsed = end - start
            worksheet.write(i + 4, 0, elapsed)
            worksheet.write(i + 4, 2, c)
            error = abs(c - opt) / opt * 100
            worksheet.write(i + 4, 4, error)

            print("\nCost: ", c)
            print("Error: " + str(round(error, 2)) + "%")
            print("Path: ", p)

        idx += 1
    input("Press any key to finish")
    wb.close()


if __name__ == "__main__":
    main()
