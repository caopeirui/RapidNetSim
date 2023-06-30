
def read_task_log(file_name):
    with open(file_name, 'r') as f:
        row_list = f.read().splitlines()
    
    start_time_dict = {}
    finish_time_dict = {}
    for row in row_list:
        _, task_id, type, time = row.split(',')
        task_id = int(task_id)
        if type == 'start_time':
            start_time_dict[task_id] = float(time)
        elif type == 'finish_time':
            finish_time_dict[task_id] = float(time)

    return start_time_dict, finish_time_dict


def test_a_task_completion_time(expected_completion_time, task_file_name, task_seq):
    start_time_dict, finish_time_dict = read_task_log(task_file_name)
    real_completion_time = finish_time_dict[task_seq] - start_time_dict[task_seq]
    try:
        assert abs(expected_completion_time - real_completion_time) <= 0.000000001
        print('The test of a task completion time is passed!!!')
    except AssertionError:
        print(f'Test failed: expected time {expected_completion_time}, real time {real_completion_time}')

if __name__ == "__main__":

    expected_completion_time = 3.857000000000000
    task_file_name = './hw_eps_all2all_hierachical/task_time.log'
    test_a_task_completion_time(expected_completion_time, task_file_name)
