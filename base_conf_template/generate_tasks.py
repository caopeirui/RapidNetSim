import random
import math
import numpy as np
import csv
import time


def _modify_to_2exponent(task_occupied_NIC_num):
    import math
    exponent = math.log2(task_occupied_NIC_num)
    exponent = math.ceil(exponent)
    exponent = max(1, exponent)
    task_occupied_NIC_num =  2 ** exponent

    return task_occupied_NIC_num


def generate_tasks(num):
    request_sequence = eval(open("../../base_conf_template/request_sequence","r").read())
    assert num <= len(request_sequence)
    task_info = request_sequence[:num]
    new_task_info = []
    arriving_time = 0
    for (_, model_size, task_occupied_NIC_num) in task_info:
        new_task_occupied_NIC_num = _modify_to_2exponent(task_occupied_NIC_num)
        new_task_info.append((arriving_time, model_size, new_task_occupied_NIC_num))
        # arriving_time += 0.1
    return new_task_info


def generate_big_custom_tasks(num, exponential_beta = 0.1, fixed_model_size = None):
    new_task_info = []
    arriving_time = 0

    base_NIC_num_list = [1, 512, 1024, 256, 512]
    num_times_list = [50, 20, 50, 60, 500]
    
    task_occupied_NIC_num_list = []
    for i in range(len(num_times_list)):
        for _ in range(num_times_list[i]):
            task_occupied_NIC_num_list.append(base_NIC_num_list[i])
    random.seed(0)
    random.shuffle(task_occupied_NIC_num_list)

    if exponential_beta != False:
        rng = np.random.default_rng(0)
        exponential_interval_list = rng.exponential(exponential_beta, num)

    j = 0
    last_arriving_time = arriving_time
    interval_list = []
    for _ in range(num):
        if fixed_model_size is None:
            model_size = random.random()
        else:
            model_size = fixed_model_size
        if exponential_beta != False:
            arriving_time += exponential_interval_list[i]
        new_task_info.append((arriving_time, model_size, task_occupied_NIC_num_list[j]))
        interval_list.append(arriving_time - last_arriving_time)
        j += 1
    print('new_task_info:', new_task_info)
    print_workload(new_task_info)
    print('average interval:', np.mean(interval_list))
    return new_task_info


def generate_custom_tasks(num, max_NIC_num = 256, exponential_beta = 0.1, fixed_model_size = None):
    new_task_info = []
    arriving_time = 0

    base_NIC_num_list = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]
    num_times_list = [50, 20, 20, 100, 100, 100, 500, 50, 60, 30]
    
    task_occupied_NIC_num_list = []
    for i in range(len(num_times_list)):
        for _ in range(num_times_list[i]):
            if base_NIC_num_list[i] > max_NIC_num:
                base_NIC_num_list[i] = max_NIC_num
            task_occupied_NIC_num_list.append(base_NIC_num_list[i])
    random.seed(0)
    random.shuffle(task_occupied_NIC_num_list)

    if exponential_beta != False:
        rng = np.random.default_rng(0)
        exponential_interval_list = rng.exponential(exponential_beta, num)

    j = 0
    last_arriving_time = arriving_time
    interval_list = []
    for _ in range(num):
        if fixed_model_size is None:
            model_size = random.random()
        else:
            model_size = fixed_model_size
        if exponential_beta != False:
            arriving_time += exponential_interval_list[i]
        new_task_info.append((arriving_time, model_size, task_occupied_NIC_num_list[j]))
        interval_list.append(arriving_time - last_arriving_time)
        j += 1
    print('new_task_info:', new_task_info)
    print_workload(new_task_info)
    print('average interval:', np.mean(interval_list))
    return new_task_info


def get_fixed_requests_256_part_tasks(num, exponential_interval = True, beta = 1, filename = '../../base_conf_template/fixed_requests_256_part.txt', modify = False, random_beta = False, beta_list = []):
    with open(filename, 'r') as f:
        row_list = f.read().splitlines()
        
    base_NIC_num_list = [1, 2, 4, 8, 16, 32, 64, 128, 256]
    temp_sum = 0
    for job_class_id in base_NIC_num_list:
        temp_sum += math.log(job_class_id)
    job_weight_map = {}
    for job_class_id in base_NIC_num_list:
        job_weight_map[job_class_id] = math.log(job_class_id)/temp_sum

    random.seed(0)

    temp_list = []
    temp_time = 0
    if exponential_interval == True and random_beta == False:
        rng = np.random.default_rng(0)
        exponential_interval_list = rng.exponential(beta, num)
    elif random_beta:
        exponential_interval_list_list = []
        for temp_beta in beta_list:
            rng = np.random.default_rng(0)
            exponential_interval_list = rng.exponential(temp_beta, num)
            exponential_interval_list_list.append(exponential_interval_list)
    new_task_info = []
    arriving_time = 0
    np.random.seed(0)
    model_size_list = np.random.normal(800,700,(num,)).tolist()
    for i in range(num):
        task_occupied_NIC_num = int(float(row_list[i].split(' ')[0]))
        temp_list.append(task_occupied_NIC_num)

        if modify == True:
            task_occupied_NIC_num = tmp_modify_occupied_NIC_num(task_occupied_NIC_num)

        #model_size = random.randint(100, 1000)
        model_size = max(100,model_size_list[i])
        #print("fuck", model_size)

        if exponential_interval == True:
            if not random_beta:
                arriving_time += exponential_interval_list[i]
            else:
                arriving_time += exponential_interval_list_list[(100*i)%(len(beta_list))][i]
            # print((arriving_time))
            # arriving_time += random_exponential(0.5)

        new_task_info.append((arriving_time, model_size, task_occupied_NIC_num))
    print('new_task_info:', new_task_info)
    return new_task_info


def tmp_modify_occupied_NIC_num(task_occupied_NIC_num):
    if task_occupied_NIC_num >= 64:
        return 64
    else:
        return task_occupied_NIC_num


def random_exponential(lam):
    # x = np.arange(0, 15, 0.1)
    # y = lam * np.exp(-lam * x)
    pv = 0.0
    pv = (random.random() % 100) / 100
    while pv == 0:
        pv = (random.random()() % 100) / 100

    pv = (-1  / lam) * math.log(1 - pv)
    print(pv)
    return pv


def date_time_str_to_long(input_date_time_string):
    if input_date_time_string == 'None':
        return 0
    timeArray = time.strptime(input_date_time_string, "%Y-%m-%d %H:%M:%S")
    
    timeStamp = int(time.mktime(timeArray))
    
    return timeStamp


def get_shangtang_tasks_old(task_num, filename = '../../base_conf_template/cluster_log.csv', exponential_beta = 0.000003):
    waiting_list = []
    running_list = []
    gpu_list = []
    new_task_info = []

    rng = np.random.default_rng(0)
    exponential_interval_list = rng.exponential(exponential_beta, task_num)
    i = 0
    with open(filename, encoding='utf-8-sig') as f:
        start_time = 0
        for row in csv.reader(f, skipinitialspace=True):
            duration_time = 0
            waiting_time = 0
            if (row[6] == 'COMPLETED') and int(row[3])>0 and date_time_str_to_long((row[7])) >= date_time_str_to_long("2020-08-20 00:51:57"): #2020-08-15 00:51:57
                if(start_time == 0):
                    start_time = date_time_str_to_long((row[7]))
                duration_time = date_time_str_to_long(row[9]) - date_time_str_to_long(row[8])
                waiting_time = date_time_str_to_long(row[8]) - date_time_str_to_long(row[7])
                running_list.append(duration_time)
                waiting_list.append(waiting_time)
                task_occupied_NIC_num = pow(2,math.ceil(math.log2(int(row[3]))))
                gpu_list.append(task_occupied_NIC_num)

                new_task_info.append((exponential_interval_list[i], 1, task_occupied_NIC_num))
                i += 1
                if i == task_num:
                    break
    
    print('debug new_task_info', new_task_info)
    return new_task_info


def get_shangtang_tasks(num, exponential_beta = 0.0001):
    new_task_info = []
    arriving_time = 0

    base_NIC_num_list = [1, 2, 4, 8, 16, 32, 64, 128, 256]
    num_times_list = [11136, 829, 1109, 4257, 400, 925, 76, 80, 13]
    
    task_occupied_NIC_num_list = []
    for i in range(len(num_times_list)):
        for _ in range(num_times_list[i]):
            task_occupied_NIC_num_list.append(base_NIC_num_list[i])
    random.seed(0)
    random.shuffle(task_occupied_NIC_num_list)

    if exponential_beta != False:
        rng = np.random.default_rng(0)
        exponential_interval_list = rng.exponential(exponential_beta, num)

    j = 0
    for _ in range(num):
        # model_size = random.random()
        model_size = 100
        if exponential_beta != False:
            arriving_time += exponential_interval_list[i]
        new_task_info.append((arriving_time, model_size, task_occupied_NIC_num_list[j]))

        j += 1

    return new_task_info


def print_workload(new_task_info):
    GPU_num_sum = 0
    simultaneous_GPU_time = 0
    full_GPU_time = 0
    for (submit_time, model_size, GPU_num) in new_task_info:
        GPU_num_sum += GPU_num
        # submit_time_sum += submit_time
        simultaneous_GPU_time += model_size * GPU_num
        full_GPU_time += model_size * GPU_num + submit_time

    print('GPU_num_sum', GPU_num_sum)
    print('simultaneous_GPU_time', simultaneous_GPU_time)
    print('full_GPU_time', full_GPU_time)
    print('workload', simultaneous_GPU_time / full_GPU_time)


def generate_16384_custom_tasks(exponential_beta = 1, fixed_model_size = None):
    new_task_info = []
    arriving_time = 0

    base_NIC_num_list = [4096, 512, 1024, 256]
    num_times_list = [5, 30, 15, 50]
    num = sum(num_times_list)
    fixed_model_size = 1

    task_occupied_NIC_num_list = []
    for i in range(len(num_times_list)):
        for _ in range(num_times_list[i]):
            task_occupied_NIC_num_list.append(base_NIC_num_list[i])
    random.seed(0)
    random.shuffle(task_occupied_NIC_num_list)

    if exponential_beta != False:
        rng = np.random.default_rng(0)
        exponential_interval_list = rng.exponential(exponential_beta, num)

    j = 0
    last_arriving_time = arriving_time
    interval_list = []
    for _ in range(num):
        if fixed_model_size is None:
            model_size = random.random()
        else:
            model_size = fixed_model_size
        if exponential_beta != False:
            arriving_time += exponential_interval_list[i]
        new_task_info.append((arriving_time, model_size, task_occupied_NIC_num_list[j]))
        interval_list.append(arriving_time - last_arriving_time)
        j += 1
    print('new_task_info:', new_task_info)
    print_workload(new_task_info)
    print('average interval:', np.mean(interval_list))
    return new_task_info

def generate_16384_custom_tasks2(num_tmp = 100, exponential_beta = 1, fixed_model_size = None):
    new_task_info = []
    arriving_time = 0

    base_NIC_num_list = [4096, 512, 1024, 256, 8192]
    if num_tmp == 100:
        num_times_list = [35, 10, 5, 10, 40]
    else:
        num_times_list = np.array([35, 10, 5, 10, 40]) * num_tmp / 100
    num = int(sum(num_times_list))
    fixed_model_size = 1

    task_occupied_NIC_num_list = []
    for i in range(len(num_times_list)):
        for _ in range(int(num_times_list[i])):
            task_occupied_NIC_num_list.append(base_NIC_num_list[i])
    random.seed(0)
    random.shuffle(task_occupied_NIC_num_list)

    if exponential_beta != False:
        rng = np.random.default_rng(0)
        exponential_interval_list = rng.exponential(exponential_beta, num)

    j = 0
    last_arriving_time = arriving_time
    interval_list = []
    for _ in range(num):
        if fixed_model_size is None:
            model_size = random.random()
        else:
            model_size = fixed_model_size
        if exponential_beta != False:
            arriving_time += exponential_interval_list[i]
        new_task_info.append((arriving_time, model_size, task_occupied_NIC_num_list[j]))
        interval_list.append(arriving_time - last_arriving_time)
        j += 1
    print('new_task_info:', new_task_info)
    print_workload(new_task_info)
    print('average interval:', np.mean(interval_list))
    return new_task_info


if __name__ == "__main__":
    print(generate_16384_custom_tasks())