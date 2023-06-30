
from code import interact
from rapidnetsim.communication_strategy.strategy_base import StrategyBase
from rapidnetsim.core.infrastructure.flow import Flow

class HierachicalAll2All(StrategyBase):
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
            round_pair_list = self.get_all_to_all_every_round_pair(task_occupied_NIC_num, model_size)
        else:
            round_pair_list = self.get_hierachical_all2all_every_round_pair(task_occupied_NIC_num, model_size, NIC_num_in_a_server)
        return round_pair_list


    def get_all_to_all_every_round_pair(self, task_occupied_NIC_num, model_size):
        """Return communication pair in every round under all-to-all strategy.
        [
            [(NIC_src, NIC_dst, communication_size), (NIC_src, NIC_dst, communication_size)] ...
            [(NIC_src, NIC_dst, communication_size), (NIC_src, NIC_dst, communication_size)], ...
            ...
        ]
        """
        all_to_all_pair_list = []
        
        round_num = task_occupied_NIC_num - 1
    
        # all_to_all
        mask = 1
        communication_size = model_size / task_occupied_NIC_num
        for _ in range(0, round_num):
            a_round = []
            for pair in range(0, task_occupied_NIC_num):
                NIC_src = pair
                NIC_dst = (pair ^ mask)
                a_round.append((NIC_src, NIC_dst, communication_size))
            all_to_all_pair_list.append(a_round)
            mask = mask + 1
        return all_to_all_pair_list


    def get_hierachical_all2all_every_round_pair(self, task_occupied_NIC_num, model_size, NIC_num_in_a_server):
        pair_list = []
        node_num = int(task_occupied_NIC_num / NIC_num_in_a_server)
        
        # intra-node all_to_all
        communication_size = model_size / NIC_num_in_a_server
        round_num = NIC_num_in_a_server - 1
        mask = 1
        for _ in range(0, round_num):
            a_round = []
            for node_id in range(node_num):
                for pair in range(0, NIC_num_in_a_server):
                    NIC_src = pair + node_id * NIC_num_in_a_server
                    NIC_dst = (pair ^ mask) + node_id * NIC_num_in_a_server
                    a_round.append((NIC_src, NIC_dst, communication_size))

            pair_list.append(a_round)
            mask = mask + 1

        # inter-node all_to_all
        mask = 1
        communication_size = model_size / node_num
        round_num = node_num - 1
        for _ in range(round_num):
            round_list = []
            for pair in range(0, node_num):
                src_server = pair
                dst_server = (pair ^ mask)
                for gpu_idx in range(NIC_num_in_a_server):
                    NIC_src = src_server * NIC_num_in_a_server + gpu_idx
                    NIC_dst = dst_server * NIC_num_in_a_server + gpu_idx
                    round_list.append((NIC_src, NIC_dst, communication_size))
            mask = mask + 1
            pair_list.append(round_list)
        return pair_list
    

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
            intra_datafactor = (task_occupied_NIC_num - 1) / task_occupied_NIC_num
            inter_datafactor = 0
        else:
            intra_datafactor = (NIC_num_in_a_server - 1) / NIC_num_in_a_server
            inter_datafactor = (task_occupied_NIC_num - NIC_num_in_a_server) / task_occupied_NIC_num
        if task_occupied_NIC_num == 1:
            intra_times = 0
            inter_times = 0
        elif task_occupied_NIC_num <= NIC_num_in_a_server:
            intra_times = task_occupied_NIC_num - 1
            inter_times = 0
        else:
            intra_times = NIC_num_in_a_server - 1
            inter_times = int(task_occupied_NIC_num / NIC_num_in_a_server) - 1
        expected_completion_time = model_size * (intra_datafactor / float(Simulator.CONF_DICT['inner_server_bandwidth']) + inter_datafactor / float(Simulator.CONF_DICT['switch_port_bandwidth'])) + intra_times * inserver_transmission_delay + inter_times * network_transmission_delay
        return expected_completion_time


if __name__ == '__main__':
    test = HierachicalAll2All()
    res = test.get_hierachical_all2all_every_round_pair(16, 4, 4)
    print(res)
