
import sys

class StrategyBase:

    def __init__(self) -> None:
        pass

    
    def deal_job(self, start_time, taskid, model_size, task_occupied_NIC_num, use_NIC_list, NIC_num_in_a_server):
        raise NotImplemented(f"NOTICE: You need to override {self.__class__}->{sys._getframe().f_code.co_name}() in a subclass!")
    

    def record_network_occupy(self, taskid, roundid, flow, src):
        from rapidnetsim.core.simulator import Simulator
        Simulator.add_a_wait_transmit_flow(taskid, roundid, flow)
        Simulator.add_flowid_into_task_record(Simulator.FLOWID, taskid)


    def get_task_a_iteration_pair_list(self, task_occupied_NIC_num, model_size, NIC_num_in_a_server, use_NIC_list):
        raise NotImplemented(f"NOTICE: You need to override {self.__class__}->{sys._getframe().f_code.co_name}() in a subclass!")
        pass

