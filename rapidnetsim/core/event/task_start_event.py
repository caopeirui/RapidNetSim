
from rapidnetsim.core.event.event import Event
from rapidnetsim.task.waiting_task import WaitingTask
import rapidnetsim.core.stage_controller as sc

class TaskStartEvent(Event):
    """Trigger flows in task when simulation time has reached arriving time.
    """
    def __init__(self, time_from_now, model_size, task_occupied_NIC_num, task_type_obj, taskid, task_type, task_iteration_num, NIC_num_in_a_server) -> None:
        super().__init__(time_from_now)
        self._time_from_now = time_from_now
        self._model_size = model_size
        self._task_occupied_NIC_num = task_occupied_NIC_num
        self._task_type_obj = task_type_obj
        self._taskid = taskid
        self._type_priority = 2

        self._task_type = task_type
        self._task_iteration_num = task_iteration_num
        self._NIC_num_in_a_server = NIC_num_in_a_server


    def __str__(self) -> str:
        print_dict = {
            'time_from_now': self._time_from_now,
            'event_time': self.get_event_time(),
            'taskid': self._taskid,
        }
        print_str = '<TaskStartEvent | '
        for key, val in print_dict.items():
            print_str += key + ': ' + str(val) + ', '
        print_str += '>'
        return print_str


    def do_sth(self):
        from rapidnetsim.core.simulator import Simulator

        task_occupied_NIC_num = self._task_occupied_NIC_num
        model_size = self._model_size
        task_type_obj = self._task_type_obj
        taskid = self._taskid

        task_type = self._task_type
        task_iteration_num = self._task_iteration_num
        NIC_num_in_a_server = self._NIC_num_in_a_server

        if len(Simulator.WAITING_TASK_LIST) == 0:
            scheduler = Simulator.get_scheduler()

            allocate_succeed, use_NIC_list = sc.allocate_a_task(scheduler, model_size, task_occupied_NIC_num, task_type_obj, taskid)
            if allocate_succeed == False:
                # If GPU resources is not enough, push the task information to global WAITING_TASK_LIST
                arriving_time = self.get_event_time()

                a_waiting_task = WaitingTask(arriving_time, model_size, task_occupied_NIC_num, task_type_obj, taskid, task_type, task_iteration_num, NIC_num_in_a_server)
                
                Simulator.push_a_waiting_task(a_waiting_task)
            else:
                sc.continue_record_more_iteration_if_need(taskid, task_occupied_NIC_num, model_size, task_type, task_type_obj, task_iteration_num, NIC_num_in_a_server, use_NIC_list)

        else:
            arriving_time = self.get_event_time()
            a_waiting_task = WaitingTask(arriving_time, model_size, task_occupied_NIC_num, task_type_obj, taskid, task_type, task_iteration_num, NIC_num_in_a_server)
            Simulator.push_a_waiting_task(a_waiting_task)

        return
