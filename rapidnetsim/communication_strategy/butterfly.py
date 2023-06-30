
import math
from rapidnetsim.communication_strategy.strategy_base import StrategyBase
from rapidnetsim.core.infrastructure.flow import Flow

class Butterfly(StrategyBase):
    def __init__(self) -> None:
        pass


    def deal_job(self, taskid, model_size, task_occupied_NIC_num, use_NIC_list, NIC_num_in_a_server):
        """The initial jobs are assigned according to communication strategy.
        """
        from rapidnetsim.core.simulator import Simulator
        from rapidnetsim.core.event.flow_transmit_event import FlowTransmitEvent

        print(f'Time {Simulator.get_current_time()} start task {taskid} occuping NIC num {len(use_NIC_list)}')
        Simulator.task_time_logger.write(f'taskid,{taskid},start_time,{Simulator.get_current_time()}\n')

        conservative = False
        if Simulator.CONF_DICT['find_next_hop_method'] == 'conservative':
            conservative = True


        # Deal with only 1 GPU occupation
        if task_occupied_NIC_num == 1:
            flow_list = []
            flow = Flow(
                Simulator.FLOWID, model_size, None, use_NIC_list[0], use_NIC_list[0],
                model_size, None,
                taskid, 0, task_occupied_NIC_num, conservative
            )
            self.record_network_occupy(taskid, 0, flow, use_NIC_list[0])
            flow_list.append(flow)
            Simulator.register_event(FlowTransmitEvent(0, flow_list))
            Simulator.FLOWID += 1
            return

        communication_size = model_size

        round_pair_list = self.get_task_a_iteration_pair_list(task_occupied_NIC_num, model_size, NIC_num_in_a_server, use_NIC_list)

        roundid = 0
        for pair_list in round_pair_list:
            # Every round
            for (src, dst) in pair_list:
                # use_NIC_list[src] maps old may-occupied NIC_id to new unoccupied NIC_id
                flow = Flow(
                    Simulator.FLOWID, communication_size, None, use_NIC_list[src], use_NIC_list[dst],
                    communication_size, None,
                    taskid, roundid, task_occupied_NIC_num
                )
                self.record_network_occupy(taskid, roundid, flow, use_NIC_list[src])
                Simulator.FLOWID += 1
            roundid += 1
            # TODO: Add computation time

        # Register first round job flows
        flow_list = []
        for flowid, flow in Simulator.get_wait_transmit_dict()[f'{taskid}_0'].items():
            flow_list.append(flow)
        Simulator.register_event(FlowTransmitEvent(0, flow_list))

    
    def get_task_a_iteration_pair_list(self, task_occupied_NIC_num, model_size, NIC_num_in_a_server, use_NIC_list):
        return self.get_butterfly_every_round_pair(task_occupied_NIC_num)


    def get_butterfly_every_round_pair(self, task_occupied_NIC_num):
        """Return communication pair in every round under butterfly strategy.
        [
            [(NIC_src, NIC_dst)], [(NIC_src, NIC_dst)] ...
            [(NIC_src, NIC_dst)], [(NIC_src, NIC_dst)], ...
            ...
        ]
        """
        butterfly_pair_list = []
        round_num = math.log2(task_occupied_NIC_num)
        assert(round_num.is_integer())
        round_num = int(round_num)
    
        mask = 1
        for _ in range(0, round_num):
            a_round = []
            for pair in range(0, task_occupied_NIC_num):
                NIC_src = pair
                NIC_dst = (pair ^ mask)
                a_round.append((NIC_src, NIC_dst))
            butterfly_pair_list.append(a_round)
            mask = mask * 2

        return butterfly_pair_list


    # def butterfly_primitive(self, node_num):
    #     node_comm_task = []
    #     for src in range(node_num):
    #         step = 2
    #         dst = -1
    #         while(step <= node_num):
    #             if(src % step < step / 2):
    #                 dst = src + step / 2
    #             else:
    #                 dst = src - step / 2
    #             node_comm_task.append([src, int(dst)])
    #             step = step * 2
    #     return node_comm_task

    def get_expected_completion_time(self, task_seq = 0):
        from rapidnetsim.core.simulator import Simulator
        task_list = eval(Simulator.CONF_DICT['task_list'])
        _, model_size, task_occupied_NIC_num = task_list[task_seq]
        NIC_num_in_a_server = int(Simulator.CONF_DICT['NIC_num_in_a_server'])
        network_transmission_delay = float(Simulator.CONF_DICT['network_transmission_delay'])
        inserver_transmission_delay = float(Simulator.CONF_DICT['inserver_transmission_delay'])
        if task_occupied_NIC_num == 1:
            intra_datafactor = 1
            inter_datafactor = 0
        elif task_occupied_NIC_num <= NIC_num_in_a_server:
            intra_datafactor = math.log2(task_occupied_NIC_num)
            inter_datafactor = 0
        else:
            intra_datafactor = math.log2(NIC_num_in_a_server)
            inter_datafactor = math.log2(task_occupied_NIC_num) - math.log2(NIC_num_in_a_server)
        if task_occupied_NIC_num == 1:
            intra_times = 0
            inter_times = 0
        elif task_occupied_NIC_num <= NIC_num_in_a_server:
            intra_times = math.log2(task_occupied_NIC_num)
            inter_times = 0
        else:
            intra_times = math.log2(NIC_num_in_a_server)
            inter_times = math.log2(task_occupied_NIC_num) - math.log2(NIC_num_in_a_server)
        expected_completion_time = model_size * (intra_datafactor / float(Simulator.CONF_DICT['inner_server_bandwidth']) + inter_datafactor / float(Simulator.CONF_DICT['switch_port_bandwidth'])) + intra_times * inserver_transmission_delay + inter_times * network_transmission_delay
        return expected_completion_time