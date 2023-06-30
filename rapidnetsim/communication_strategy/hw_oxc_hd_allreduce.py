
import math
from rapidnetsim.communication_strategy.strategy_base import StrategyBase
from rapidnetsim.core.infrastructure.flow import Flow

class HwOxcHdAllreduce(StrategyBase):
    def __init__(self) -> None:
        pass


    def deal_job(self, taskid, model_size, task_occupied_NIC_num, use_NIC_list, NIC_num_in_a_server):
        """The initial jobs are assigned according to communication strategy.
        """
        from rapidnetsim.core.simulator import Simulator
        from rapidnetsim.core.event.flow_transmit_event import FlowTransmitEvent

        print(f'Time {Simulator.get_current_time()} start task {taskid} occuping NIC num {len(use_NIC_list)}')
        Simulator.task_time_logger.write(f'taskid,{taskid},start_time,{Simulator.get_current_time()}\n')

        # Deal with only 1 GPU occupation
        if task_occupied_NIC_num == 1:
            flow_list = []
            flow = Flow(
                Simulator.FLOWID, model_size, None, use_NIC_list[0], use_NIC_list[0],
                model_size, None,
                taskid, 0, task_occupied_NIC_num, False, use_NIC_list,
            )
            self.record_network_occupy(taskid, 0, flow, use_NIC_list[0])
            flow_list.append(flow)
            Simulator.register_event(FlowTransmitEvent(0, flow_list))
            Simulator.FLOWID += 1
            return

        round_pair_list = self.get_task_a_iteration_pair_list(task_occupied_NIC_num, model_size, NIC_num_in_a_server, use_NIC_list)

        roundid = 0
        for pair_list in round_pair_list:
            # Every round
            for (src, dst, communication_size) in pair_list:
                # use_NIC_list[src] maps old may-occupied NIC_id to new unoccupied NIC_id
                flow = Flow(
                    Simulator.FLOWID, communication_size, None, use_NIC_list[src], use_NIC_list[dst],
                    communication_size, None,
                    taskid, roundid, task_occupied_NIC_num, False, use_NIC_list,
                )
                self.record_network_occupy(taskid, roundid, flow, use_NIC_list[src])
                Simulator.FLOWID += 1
            roundid += 1


        # Register first round job flows
        flow_list = []
        for flowid, flow in Simulator.get_wait_transmit_dict()[f'{taskid}_0'].items():
            flow_list.append(flow)
        Simulator.register_event(FlowTransmitEvent(0, flow_list))


    def get_task_a_iteration_pair_list(self, task_occupied_NIC_num, model_size, NIC_num_in_a_server, use_NIC_list):
        if task_occupied_NIC_num <= NIC_num_in_a_server:
            round_pair_list = self.get_ring_every_round_pair(task_occupied_NIC_num, model_size)
        else:
            round_pair_list = self.get_hw_oxc_allreduce_every_round_pair(task_occupied_NIC_num, model_size, NIC_num_in_a_server)
        return round_pair_list


    def get_ring_every_round_pair(self, task_occupied_NIC_num, model_size):
        """Return communication pair in every round under ring strategy.
        [
            [(NIC_src, NIC_dst)], [(NIC_src, NIC_dst)] ...
            [(NIC_src, NIC_dst)], [(NIC_src, NIC_dst)], ...
            ...
        ]
        """
        ring_pair_list = []
        round_num = 2 * (task_occupied_NIC_num - 1)
        communication_size =  model_size / task_occupied_NIC_num / 2
        for _ in range(round_num):
            forward = []
            backward = []
            for i in range(task_occupied_NIC_num):
                src = i
                if i == task_occupied_NIC_num - 1:
                    dst = 0
                else:
                    dst = i + 1
                forward.append((src, dst,  communication_size))
                backward.append((dst, src, communication_size))
            ring_pair_list.append(forward + backward)

        return ring_pair_list


    def get_hw_oxc_allreduce_every_round_pair(self, task_occupied_NIC_num, model_size, NIC_num_in_a_server):
        hd_pair_list = []
        node_num = int(task_occupied_NIC_num / NIC_num_in_a_server)
        mask = 1
        communication_size = model_size / 2
        while mask < NIC_num_in_a_server:
            round = []
            for src in range(0, NIC_num_in_a_server):
                dst = src ^ mask
                for node in range(0, node_num):
                    round.append((src + node * NIC_num_in_a_server, dst + node * NIC_num_in_a_server, communication_size))
            hd_pair_list.append(round)
            mask *= 2
            communication_size /= 2
        # allreduce in a mesh topology
        forward = []
        backward = []
        for i in range(node_num):  # assume that NIC_num_in_a_server == num_node
            dst = i * NIC_num_in_a_server + i
            for j in range(NIC_num_in_a_server):
                if i == j:
                    continue
                src = j * NIC_num_in_a_server + i
                forward.append((src, dst, model_size / NIC_num_in_a_server))
                backward.append((dst, src, model_size / NIC_num_in_a_server))
        hd_pair_list.append(forward)
        hd_pair_list.append(backward)
        # allgather
        mask = 1
        communication_size = model_size / NIC_num_in_a_server
        while mask < NIC_num_in_a_server:
            round = []
            for src in range(0, NIC_num_in_a_server):
                dst = src ^ mask
                for node in range(0, node_num):
                    round.append((src + node * NIC_num_in_a_server, dst + node * NIC_num_in_a_server, communication_size))
            hd_pair_list.append(round)
            mask *= 2
            communication_size *= 2

        return hd_pair_list

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
            intra_datafactor = 2 * (task_occupied_NIC_num - 1) / task_occupied_NIC_num
            inter_datafactor = 0
        else:
            intra_datafactor = 2 * (1 - 1 / NIC_num_in_a_server)
            inter_datafactor = 2 * (1 - 1 / NIC_num_in_a_server)
        if task_occupied_NIC_num == 1:
            intra_times = 0
            inter_times = 0
        elif task_occupied_NIC_num <= NIC_num_in_a_server:
            intra_times = 4 * (task_occupied_NIC_num - 1)
            inter_times = 0
        else:
            intra_times = 2 * math.log2(NIC_num_in_a_server)
            inter_times = 2 * (NIC_num_in_a_server - 1)
        expected_completion_time = model_size * (intra_datafactor / float(Simulator.CONF_DICT['inner_server_bandwidth']) + inter_datafactor / float(Simulator.CONF_DICT['switch_port_bandwidth'])) + intra_times * inserver_transmission_delay + inter_times * network_transmission_delay
        return expected_completion_time


if __name__ == '__main__':
    test = HwOxcHdAllreduce()
    res = test.get_hw_oxc_allreduce_every_round_pair(16, 4, 4)
    print(res)
