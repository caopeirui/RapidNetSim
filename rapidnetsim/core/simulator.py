
import random
import heapq

from rapidnetsim.core.event.event import Event
from rapidnetsim.core.infrastructure.flow import Flow
from rapidnetsim.conf.global_conf import GlobalConf
from rapidnetsim.core.infrastructure.infra_base import InfraBase
from rapidnetsim.core.network_refresh import refresh_taskstep_finish_event
from rapidnetsim.scheduler.hw_oxc.hw_oxc_scheduler2 import HwOxcScheduler2

class Simulator:
    """Simulator takes charge of the global management of
    config, simulation time, events and random module etc.
    So its member functions are mostly static methods.
    """

    FLOWID = 0

    _task_record_dict = {}      # {'taskid': flowid}
    _wait_transmit_dict = {}    # {'taskid_roundid': {'flowid', Flow}, ...}

    _taskstep_info_dict = {}

    WAITING_TASK_LIST = []      # [WaitingTask obj, WaitingTask obj, ...] should be used through heapq.

    ITERATION_FINISH_ROUNDID_DICT = {}        # {'taskid': [finishflag roundid, finishflag roundid, ...]}

    LINK_OCCUPIED_FOR_TASKS = {}

    INTRA_SERVER_LINK_OCCUPIED_CNT = {}

    TASK_SWITCH_DICT = {}    # {taskid: switch_list on the top of mesh_sheduler} for mesh_scheduler
    TASK_NIC_DICT = {}       # {taskid: need_NIC_list on the top of mesh_sheduler} for mesh_scheduler

    CONF_DICT = {}

    LAST_TASKSTEPFINISHEVENT = None

    TASK_FULL_OCS_PREPARE_DICT = {}

    TASK_STEP_LINK_OCCUPY = {}

    CONFLICT_TASKSTEPFLOW_RECORD = 0


    def __init__(self) -> None:
        raise Exception("Simulator acts as global static class and should not be instantiated!")


    @staticmethod
    def setup(conf_handler):
        """The seting up of simulation stage.
        Set: 
            - the global random seed.
            - simulation time.
            - event queue.
        """
        Simulator._current_time = 0      # Simulation time
        Simulator._event_q = []

        if conf_handler['Parameter'].get('seed') is None:
            Simulator._set_random_seed(999)
        else:
            Simulator._set_random_seed(conf_handler['Parameter'].get('seed'))

        Simulator._global_conf = GlobalConf(conf_handler)
        
        conf_parameter = Simulator._global_conf._config_handler['Parameter']
        for item in conf_parameter:
            Simulator.CONF_DICT[item] = conf_parameter[item]
        conf_task = Simulator._global_conf._config_handler['Task']
        for item in conf_task:
            Simulator.CONF_DICT[item] = conf_task[item]
        conf_topology = Simulator._global_conf._config_handler['Topology']
        for item in conf_topology:
            Simulator.CONF_DICT[item] = conf_topology[item]

        
        if Simulator.CONF_DICT.get('network_transmission_delay') is None or Simulator.CONF_DICT.get('network_transmission_delay') == '':
            Simulator.CONF_DICT['network_transmission_delay'] = '0'
        if Simulator.CONF_DICT.get('inserver_transmission_delay') is None or Simulator.CONF_DICT.get('inserver_transmission_delay') == '':
            Simulator.CONF_DICT['inserver_transmission_delay'] = '0'
        if Simulator.CONF_DICT.get('non_overlap_ratio') is None or Simulator.CONF_DICT.get('non_overlap_ratio') == '':
            Simulator.CONF_DICT['non_overlap_ratio'] = '0.1'


        if 'yes' in Simulator.CONF_DICT['reconfiguration'] or 'no' in Simulator.CONF_DICT['reconfiguration']:
            pass
        else:
            print('Need to explicitly set reconfiguration')
            exit()


    @staticmethod
    def create_infrastructure():

        Simulator._infra_base = InfraBase()

        connect_info_list = Simulator.get_global_conf().get_connect_info_list()

        # Create network topology
        Simulator._infra_base.create_topology(connect_info_list)
        print('Create topology.', flush = True)

        scheduler_type = Simulator.CONF_DICT['joint_scheduler']
        if scheduler_type in ['hw_eps_all2all', 'hw_eps_all2all2',
                              'hw_eps_all2all_old', 'hw_eps_all2all_hierachical', 'hw_eps_hdallreduce', 'hw_eps_allreduce']:
            # Find all paths in advance
            print('Finding all paths in advance start.', flush = True)
            # -2 means no reconfiguration
            Simulator._infra_base.find_all_path(-2)
            print('Finding all paths in advance is done.', flush = True)
        
        allow_type_list = [
            'hw_eps_all2all', 'hw_eps_all2all_old', 'hw_eps_all2all2',
            'hw_eps_hdallreduce', 'hw_eps_allreduce',
            'hw_oxc_all2all', 'hw_oxc_all2all2', 'hw_oxc_all2all_sz',
            'hw_eps_all2all_hierachical', 'hw_oxc_allreduce', 'hw_oxc_hdallreduce', 'hw_oxc_allreduce_nopeer'
        ]
        assert scheduler_type in allow_type_list


    @staticmethod
    def reconfigure(delta_connect_info_list, taskid):
        Simulator._infra_base.reconfigure_topo(delta_connect_info_list, taskid)
        Simulator._infra_base.find_all_path(taskid)
        print('Update topology and path dict are done!', flush = True)


    @staticmethod
    def get_infrastructure():
        return Simulator._infra_base


    @staticmethod
    def reset():
        Simulator._current_time = 0
        Simulator._event_q.clear()


    @staticmethod
    def core_run():
        event = None
        while len(Simulator._event_q) > 0:
            event = heapq.heappop(Simulator._event_q)
            Simulator._current_time = event.get_event_time()

            # Fix the bug of repeating TaskStepFinishEvent
            if event.get_active_status() == False:
                continue
            event.do_sth()

            if len(Simulator._event_q) == 0:
                refresh_taskstep_finish_event()
            elif Simulator._event_q[0].get_event_time() > Simulator._current_time:
                refresh_taskstep_finish_event()

        Simulator.flush_logger()

        if len(Simulator.WAITING_TASK_LIST) > 0:
            # print("Warning: some task is not completed!!!")
            from rapidnetsim.core.stage_controller import _detect_and_trigger_a_task
            _detect_and_trigger_a_task()
            Simulator.core_run()


    @staticmethod
    def register_event(event: Event):
        heapq.heappush(Simulator._event_q, event)


    @staticmethod
    def get_current_time():
        """Return current simulation time.
        """
        return Simulator._current_time


    @staticmethod
    def get_plan_event_time(relative_time_from_now):
        """Return the time of triggering the event,
        that is Simulator.get_current_time() + relative_time_from_now.
        This is used to plan events in the future.
        """
        return Simulator._current_time + relative_time_from_now


    @staticmethod
    def _set_random_seed(seed):
        random.seed(seed)


    @staticmethod
    def get_global_conf():
        return Simulator._global_conf


    @staticmethod
    def get_task_record_dict():
        """{'taskid': flowid, ...}
        """
        return Simulator._task_record_dict


    @staticmethod
    def add_flowid_into_task_record(flowid, taskid):
        if Simulator._task_record_dict.get(taskid):
            Simulator._task_record_dict[taskid].append(flowid)
        else:
             Simulator._task_record_dict[taskid] = [flowid]


    @staticmethod
    def del_flowid_from_task_record(flowid, taskid):
        Simulator._task_record_dict[taskid].remove(flowid)


    @staticmethod
    def is_taskid_done(taskid):
        if len(Simulator._task_record_dict[taskid]) == 0:
            return True
        else:
            return False


    @staticmethod
    def whether_belong_the_same_server(NIC_src, NIC_dst):
        # TODO: Use the_same_server_record
        NIC_num_in_a_server = int(Simulator.CONF_DICT['NIC_num_in_a_server'])
        if NIC_src // NIC_num_in_a_server == NIC_dst // NIC_num_in_a_server:
            return True
        else:
            return False


    @staticmethod
    def get_wait_transmit_dict():
        """
        {'taskid_roundid': {'flowid', Flow}, ...}
        """
        return Simulator._wait_transmit_dict

    
    @staticmethod
    def value_in_wait_transmit_dict_is_empty():
        flag = True
        for k, v in Simulator._wait_transmit_dict.items():
            if len(v) > 0:
                flag = False
        return flag


    @staticmethod
    def add_a_wait_transmit_flow(taskid, stepid, flow: Flow):
        """
        {'stepid': {'flowid', Flow}, ...}
        """
        flowid = flow.get_flowid()
        if Simulator._wait_transmit_dict.get(f'{taskid}_{stepid}') is None:
            Simulator._wait_transmit_dict[f'{taskid}_{stepid}'] = {}
        Simulator._wait_transmit_dict[f'{taskid}_{stepid}'][flowid] = flow


    @staticmethod
    def del_a_wait_transmit_flow(taskid, stepid):
        del Simulator._wait_transmit_dict[f'{taskid}_{stepid}']


    @staticmethod
    def get_final_roundid(taskid):
        key_list = Simulator._wait_transmit_dict.keys()
        roundid_list = []
        for key in key_list:
            if f'{taskid}_' in key:
                roundid_list.append(int(key.split('_')[1]))
        return max(roundid_list)


    @staticmethod
    def load_scheduler():
        NIC_num = int(Simulator.CONF_DICT['NIC_num'])

        if Simulator.CONF_DICT['joint_scheduler'] in ['hw_oxc_all2all', 'hw_oxc_all2all_sz', 'hw_oxc_all2all2', 'hw_oxc_allreduce', 'hw_oxc_hdallreduce', 'hw_oxc_allreduce_nopeer']:
            NIC_num_in_a_server = int(Simulator.CONF_DICT['NIC_num_in_a_server'])
            Simulator._scheduler = HwOxcScheduler2(NIC_num_in_a_server, NIC_num)
        elif Simulator.CONF_DICT['joint_scheduler'] in ['hw_eps_all2all', 'hw_eps_all2all_old', 'hw_eps_all2all2', 'hw_eps_all2all_hierachical', 'hw_eps_hdallreduce', 'hw_eps_allreduce']:
            NIC_num_in_a_server = int(Simulator.CONF_DICT['NIC_num_in_a_server'])
            Simulator._scheduler = HwOxcScheduler2(NIC_num_in_a_server, NIC_num)


    @staticmethod
    def get_scheduler():
        return Simulator._scheduler


    @staticmethod
    def init_logger():
        Simulator.task_time_logger = open('./task_time.log', 'w')
        
        Simulator.occupied_num_logger = open('./occupied_num.log', 'w')
        Simulator.occupied_num_logger.write('time,unoccupied_num,taskid,task_occupied_NIC_num\n')
        
        Simulator.waiting_task_logger = open('./waiting_task.log', 'w')
        Simulator.waiting_task_logger.write('time,waiting_task_num\n')


    @staticmethod
    def clos_logger():
        Simulator.task_time_logger.close()
        Simulator.occupied_num_logger.close()
        Simulator.waiting_task_logger.close()
    

    @staticmethod
    def flush_logger():
        Simulator.task_time_logger.flush()
        Simulator.occupied_num_logger.flush()
        Simulator.waiting_task_logger.flush()


    @staticmethod
    def is_spine_switch(nodeid):
        spine_switch_num = int(Simulator.CONF_DICT['spine_switch_num'])
        leaf_switch_num = int(Simulator.CONF_DICT['leaf_switch_num'])
        NIC_num = int(Simulator.CONF_DICT['NIC_num'])
        if NIC_num + leaf_switch_num <= nodeid < NIC_num + leaf_switch_num + spine_switch_num:
            return True
        else:
            return False


    @staticmethod
    def is_leaf_switch(nodeid):
        leaf_switch_num = int(Simulator.CONF_DICT['leaf_switch_num'])
        NIC_num = int(Simulator.CONF_DICT['NIC_num'])
        if NIC_num <= nodeid < NIC_num + leaf_switch_num:
            return True
        else:
            return False

    
    @staticmethod
    def is_GPU(nodeid):
        NIC_num = int(Simulator.CONF_DICT['NIC_num'])
        if nodeid < NIC_num:
            return True
        else:
            return False


    @staticmethod
    def push_a_waiting_task(a_waiting_task):
        heapq.heappush(Simulator.WAITING_TASK_LIST, a_waiting_task)


    @staticmethod
    def pop_a_waiting_task():
        job_class_queuelength_map = {}
        for temp_task in Simulator.WAITING_TASK_LIST:
            if temp_task._task_occupied_NIC_num not in job_class_queuelength_map:
                job_class_queuelength_map[temp_task._task_occupied_NIC_num] = 0
            job_class_queuelength_map[temp_task._task_occupied_NIC_num] += 1
        for temp_task in Simulator.WAITING_TASK_LIST:
            temp_task._queue_length = job_class_queuelength_map[temp_task._task_occupied_NIC_num]
        for temp_task in Simulator.WAITING_TASK_LIST:
            if len(Simulator.WAITING_TASK_LIST)>6:
                temp_task._weight_length = -temp_task._task_occupied_NIC_num
            else:
                temp_task._weight_length = -temp_task._taskid
        return heapq.heappop(Simulator.WAITING_TASK_LIST)


    @staticmethod
    def set_NIC_to_spine_map(nic_id, spine_id):
        Simulator.get_infrastructure().get_device(nic_id).set_to_spine_id(spine_id)


    @staticmethod
    def add_link_occupied_for_tasks(taskid, src, dst, relative_port):
        if Simulator.LINK_OCCUPIED_FOR_TASKS.get((src, dst, relative_port)):
            Simulator.CONFLICT_TASKSTEPFLOW_RECORD += 1
            Simulator.LINK_OCCUPIED_FOR_TASKS[(src, dst, relative_port)].append(taskid)
        else:
            Simulator.LINK_OCCUPIED_FOR_TASKS[(src, dst, relative_port)] = [taskid]


    @staticmethod
    def del_link_occupied_for_tasks(taskid, src, dst, relative_port):
        Simulator.LINK_OCCUPIED_FOR_TASKS[(src, dst, relative_port)].remove(taskid)


    @staticmethod
    def get_link_occupied_for_tasks(src, dst, relative_port):
        return Simulator.LINK_OCCUPIED_FOR_TASKS[(src, dst, relative_port)]


    @staticmethod
    def add_task_step_link_occupy(taskid, stepid, tmp_src, next_hop, relative_port):
        if not Simulator.TASK_STEP_LINK_OCCUPY.get(taskid):
            Simulator.TASK_STEP_LINK_OCCUPY[taskid] = {}
        if Simulator.TASK_STEP_LINK_OCCUPY[taskid].get(stepid):
            Simulator.TASK_STEP_LINK_OCCUPY[taskid][stepid].append((tmp_src, next_hop, relative_port))
        else:
            Simulator.TASK_STEP_LINK_OCCUPY[taskid][stepid] = [(tmp_src, next_hop, relative_port)]

        Simulator.add_link_occupied_for_tasks(taskid, tmp_src, next_hop, relative_port)


    @staticmethod
    def del_task_step_link_occupy(taskid, stepid):
        del Simulator.TASK_STEP_LINK_OCCUPY[taskid][stepid]


    @staticmethod
    def get_task_step_link_occupy(taskid, stepid):
        return Simulator.TASK_STEP_LINK_OCCUPY[taskid][stepid]


    @staticmethod
    def set_inflight_taskstep_info(taskid, taskstep_obj):
        Simulator._taskstep_info_dict[taskid] = taskstep_obj


    @staticmethod
    def del_inflight_taskstep_info(taskid):
        del Simulator._taskstep_info_dict[taskid]


    @staticmethod
    def get_inflight_taskstep_info():
        return Simulator._taskstep_info_dict
