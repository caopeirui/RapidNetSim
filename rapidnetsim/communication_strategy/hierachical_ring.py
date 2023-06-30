

from rapidnetsim.communication_strategy.strategy_base import StrategyBase
from rapidnetsim.core.infrastructure.flow import Flow

class HierachicalRing(StrategyBase):
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
            round_pair_list = self.get_multi_server_every_round_pair(task_occupied_NIC_num, model_size, NIC_num_in_a_server)
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


    def get_multi_server_every_round_pair(self, task_occupied_NIC_num, model_size, NIC_num_in_a_server):
        pair_list = []
        node_num = int(task_occupied_NIC_num / NIC_num_in_a_server)

        communication_size = model_size / node_num
        # ring allreduce in the intra-server
        round_num = NIC_num_in_a_server - 1
        for _ in range(round_num):
            forward = []
            for i in range(NIC_num_in_a_server):
                src = i
                if i == NIC_num_in_a_server - 1:
                    dst = 0
                else:
                    dst = i + 1
                for j in range(node_num):
                    forward.append((src + j * NIC_num_in_a_server, dst + j * NIC_num_in_a_server, communication_size))
            pair_list.append(forward)
        
        # ring allreduce inter servers
        round_num = node_num - 1
        for _ in range(round_num):
            forward = []
            for i in range(round_num):
                src = i
                if i == node_num - 1:
                    dst = 0
                else:
                    dst = i + 1
                for j in range(NIC_num_in_a_server):
                    forward.append((src * NIC_num_in_a_server + j, dst * NIC_num_in_a_server + j, communication_size))
            pair_list.append(forward)


        # ring allreduce in the intra-server
        round_num = NIC_num_in_a_server - 1
        for _ in range(round_num):
            forward = []
            for i in range(NIC_num_in_a_server):
                src = i
                if i == NIC_num_in_a_server - 1:
                    dst = 0
                else:
                    dst = i + 1
                for j in range(node_num):
                    forward.append((src + j * NIC_num_in_a_server, dst + j * NIC_num_in_a_server, communication_size))
            pair_list.append(forward)

        return pair_list

    def get_expected_completion_time(self, task_seq = 0):
        pass

if __name__ == '__main__':
    test = HierachicalRing()
    res = test.get_multi_server_every_round_pair(16, 4, 4)
    print(len(res))
