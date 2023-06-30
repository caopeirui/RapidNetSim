
import math
from rapidnetsim.core.event.task_start_event import TaskStartEvent
from rapidnetsim.communication_strategy.ring import Ring
from rapidnetsim.communication_strategy.butterfly import Butterfly
from rapidnetsim.communication_strategy.butterfly2 import Butterfly2
from rapidnetsim.communication_strategy.butterfly3 import Butterfly3
from rapidnetsim.communication_strategy.all_to_all import AllToAll
from rapidnetsim.communication_strategy.hierachical_all2all import HierachicalAll2All
from rapidnetsim.communication_strategy.hw_oxc_all2all import HwOxcAll2All
from rapidnetsim.communication_strategy.hw_eps_allreduce import HwEpsAllreduce
from rapidnetsim.communication_strategy.hw_oxc_allreduce_nopeer import HwOxcAllreduceNopeer
from rapidnetsim.communication_strategy.hw_oxc_hd_allreduce import HwOxcHdAllreduce

class Task:
    def __init__(self) -> None:
        pass


    def generate(self):
        from rapidnetsim.core.simulator import Simulator

        task_type = Simulator.CONF_DICT['task_type']
        print('Task communication starategy:', task_type)
        task_list = eval(Simulator.CONF_DICT['task_list'])

        if task_type == 'all_to_all':
            task_type_obj = AllToAll()
        elif task_type == 'hierachical_all2all':
            task_type_obj = HierachicalAll2All()
        elif task_type == 'ring':
            task_type_obj = Ring()
        elif task_type == 'butterfly':
            task_type_obj = Butterfly()
        elif task_type == 'butterfly2':
            task_type_obj = Butterfly2()
        elif task_type == 'butterfly3':
            task_type_obj = Butterfly3()
        elif task_type == 'hw_oxc_all2all':
            task_type_obj = HwOxcAll2All()
        elif task_type == 'hw_eps_all2all_old':
            task_type_obj = AllToAll()
        elif task_type == 'hw_eps_all2all_hierachical':
            task_type_obj = HierachicalAll2All()
        elif task_type == 'hw_eps_all2all':
            task_type_obj = HwOxcAll2All()
        elif task_type == 'hw_oxc_allreduce_nopeer':
            task_type_obj = HwOxcAllreduceNopeer()
        elif task_type == 'hw_oxc_hdallreduce':
            task_type_obj = HwOxcHdAllreduce()
        elif task_type == 'hw_eps_hdallreduce':
            task_type_obj = HwOxcHdAllreduce()
        elif task_type == 'hw_eps_allreduce':
            task_type_obj = HwEpsAllreduce()
        
        Simulator._task_type_obj = task_type_obj

        taskid = 0
        # Generate numerous jobs through call TaskStartEvent.
        task_iteration_num = int(Simulator.CONF_DICT['task_iteration_num'])
        NIC_num_in_a_server = int(Simulator.CONF_DICT['NIC_num_in_a_server'])
        for (arriving_time, model_size, task_occupied_NIC_num) in task_list:
            Simulator.task_time_logger.write(f'taskid,{taskid},arriving_time,{arriving_time}\n')

            Simulator.register_event(
                TaskStartEvent(
                    arriving_time,
                    model_size,
                    task_occupied_NIC_num,
                    task_type_obj,
                    taskid,
                    task_type, task_iteration_num, NIC_num_in_a_server,
                )
            )
            taskid += 1
