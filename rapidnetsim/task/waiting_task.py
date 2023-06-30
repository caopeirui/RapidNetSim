from rapidnetsim.core.simulator import Simulator

class WaitingTask:
    def __init__(self, arriving_time, model_size, task_occupied_NIC_num, task_type_obj, taskid, task_type, task_iteration_num, NIC_num_in_a_server) -> None:
        self._arriving_time = arriving_time
        self._model_size = model_size
        self._task_occupied_NIC_num = task_occupied_NIC_num
        self._task_type_obj = task_type_obj
        self._taskid = taskid
        self._queue_length = -1
        self._weight_length = -1

        self._task_type = task_type
        self._task_iteration_num = task_iteration_num
        self._NIC_num_in_a_server = NIC_num_in_a_server


    def __str__(self) -> str:
        print_dict = {
            '_arriving_time': self._arriving_time,
            '_model_size': self._model_size,
            '_task_occupied_NIC_num': self._task_occupied_NIC_num,
            '_taskid': self._taskid,
            '_task_type': self._task_type,
        }
        print_str = '<WaitingTask | '
        for key, val in print_dict.items():
            print_str += key + ': ' + str(val) + ', '
        print_str += '>'
        return print_str

    def __lt__(self, other):
        waiting_task_order_mode = Simulator.CONF_DICT['waiting_task_order_mode']
        if waiting_task_order_mode == 'FIFO':
            return self._taskid < other._taskid
        elif waiting_task_order_mode == 'few_GPU_first':
            return self._task_occupied_NIC_num < other._task_occupied_NIC_num
        elif waiting_task_order_mode == 'small_task_first':
            return self._model_size < other._model_size
        elif waiting_task_order_mode == 'max_weight_matching':
            return self._queue_length > other._queue_length
        elif waiting_task_order_mode == 'dynamic_matching':
            return self._weight_length > other._weight_length
        else:
            raise Exception('The waiting_task_order_mode does not exist!')


    def get_task_info_tuple(self):
        arriving_time = self._arriving_time
        model_size = self._model_size
        task_occupied_NIC_num  = self._task_occupied_NIC_num
        task_type_obj = self._task_type_obj
        taskid = self._taskid

        task_type = self._task_type
        task_iteration_num = self._task_iteration_num
        NIC_num_in_a_server = self._NIC_num_in_a_server
        return (arriving_time, model_size, task_occupied_NIC_num, task_type_obj, taskid, task_type, task_iteration_num, NIC_num_in_a_server)