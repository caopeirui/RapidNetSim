
import math
from rapidnetsim.communication_strategy.strategy_base import StrategyBase
from rapidnetsim.core.infrastructure.flow import Flow

class HwOxcAllreduceNopeer(StrategyBase):
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
                taskid, 0, task_occupied_NIC_num, False, use_NIC_list
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
                    taskid, roundid, task_occupied_NIC_num, False, use_NIC_list
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
        
        server_set = set()
        for nic in use_NIC_list:
            server_set.add(nic // NIC_num_in_a_server)
        server_num = len(server_set)
        # TODO: different results according to the number of occupied servers.
        threshold = 4
        if task_occupied_NIC_num <= NIC_num_in_a_server:
            round_pair_list = self._get_ring_every_round_pair(task_occupied_NIC_num, model_size)
        elif server_num <= threshold:
            round_pair_list = self._get_hw_hierachical_ring_allreduce_every_round_pair(task_occupied_NIC_num, model_size, NIC_num_in_a_server)
        else:
            round_pair_list = self._get_hw_oxc_allreduce5step_every_round_pair(task_occupied_NIC_num, model_size, NIC_num_in_a_server)
        return round_pair_list


    def _get_ring_every_round_pair(self, task_occupied_NIC_num, model_size):
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


    def _get_hw_hierachical_ring_allreduce_every_round_pair(self, task_occupied_NIC_num, model_size, NIC_num_in_a_server):
        pair_list = []        
        server_num = task_occupied_NIC_num // NIC_num_in_a_server

        ring_hd_threshold = 8

        if NIC_num_in_a_server > ring_hd_threshold:
            mask = 1
            communication_size = model_size / 2
            while mask < NIC_num_in_a_server:
                round = []
                for src in range(0, NIC_num_in_a_server):
                    dst = src ^ mask
                    for node in range(0, server_num):
                        round.append((src + node * NIC_num_in_a_server, dst + node * NIC_num_in_a_server, communication_size))
                pair_list.append(round)
                mask *= 2
                communication_size /= 2
        else:
            round_num = NIC_num_in_a_server - 1
            communication_size = model_size / NIC_num_in_a_server / 2
            for _ in range(round_num):
                forward = []
                backward = []
                for i in range(NIC_num_in_a_server):
                    src = i
                    if i == NIC_num_in_a_server - 1:
                        dst = 0
                    else:
                        dst = i + 1
                    for j in range(server_num):
                        forward.append((src + j * NIC_num_in_a_server, dst + j * NIC_num_in_a_server, communication_size))
                        backward.append((dst + j * NIC_num_in_a_server, src + j * NIC_num_in_a_server, communication_size))
                pair_list.append(forward + backward)

        # accumulation for all GPUs
        # This ring allreduce is unidirectional
        # server_num is small, use ring allreduce
        second_stage_communication_size = model_size / server_num / NIC_num_in_a_server
        second_stage_round_num = 2 * (server_num - 1)
        for _ in range(second_stage_round_num):
            forward = []
            for base in range(NIC_num_in_a_server):
                for i in range(server_num):
                    src = base + i * NIC_num_in_a_server
                    if i == server_num - 1:
                        dst = base
                    else:
                        dst = base + (i + 1) * NIC_num_in_a_server
                    forward.append((src, dst, second_stage_communication_size))
            pair_list.append(forward)

        # ring for GPUs under every server
        if NIC_num_in_a_server > ring_hd_threshold:
            mask = 1
            communication_size = model_size / NIC_num_in_a_server
            while mask < NIC_num_in_a_server:
                round = []
                for src in range(0, NIC_num_in_a_server):
                    dst = src ^ mask
                    for node in range(0, server_num):
                        round.append((src + node * NIC_num_in_a_server, dst + node * NIC_num_in_a_server, communication_size))
                pair_list.append(round)
                mask *= 2
                communication_size *= 2
        else:
            for _ in range(round_num):
                forward = []
                backward = []
                for i in range(NIC_num_in_a_server):
                    src = i
                    if i == NIC_num_in_a_server - 1:
                        dst = 0
                    else:
                        dst = i + 1
                    for j in range(server_num):
                        forward.append((src + j * NIC_num_in_a_server, dst + j * NIC_num_in_a_server, communication_size))
                        backward.append((dst + j * NIC_num_in_a_server, src + j * NIC_num_in_a_server, communication_size))
                pair_list.append(forward + backward)

        return pair_list


    def _get_hw_oxc_allreduce5step_every_round_pair(self, task_occupied_NIC_num, model_size, NIC_num_in_a_server):
        from rapidnetsim.core.simulator import Simulator
        pair_list = []
        assert(task_occupied_NIC_num % NIC_num_in_a_server == 0)
        server_num = task_occupied_NIC_num // NIC_num_in_a_server
        assert(NIC_num_in_a_server % server_num == 0)
        num_partitions = NIC_num_in_a_server // server_num

        ring_hd_threshold = 8

        # step 1: reduce-scatter
        if NIC_num_in_a_server > ring_hd_threshold:
            mask = 1
            communication_size = model_size / 2
            while mask < NIC_num_in_a_server:
                round = []
                for src in range(0, NIC_num_in_a_server):
                    dst = src ^ mask
                    for node in range(0, server_num):
                        round.append((src + node * NIC_num_in_a_server, dst + node * NIC_num_in_a_server, communication_size))
                pair_list.append(round)
                mask *= 2
                communication_size /= 2
        else:
            round_num = NIC_num_in_a_server - 1
            communication_size = model_size / NIC_num_in_a_server / 2
            for _ in range(round_num):
                forward = []
                backward = []
                for i in range(NIC_num_in_a_server):
                    src = i
                    if i == NIC_num_in_a_server - 1:
                        dst = 0
                    else:
                        dst = i + 1
                    for j in range(server_num):
                        forward.append((src + j * NIC_num_in_a_server, dst + j * NIC_num_in_a_server, communication_size))
                        backward.append((dst + j * NIC_num_in_a_server, src + j * NIC_num_in_a_server, communication_size))
                pair_list.append(forward + backward)

        # step 2: inter-server mesh communication
        communication_size = model_size / NIC_num_in_a_server
        round_list = []
        for src_server in range(server_num):
            for dst_server in range(server_num):
                if src_server == dst_server:
                    continue
                for k in range(num_partitions):
                    src = src_server * NIC_num_in_a_server + dst_server * num_partitions + k
                    dst = dst_server * NIC_num_in_a_server + src_server * num_partitions + k
                # other flows have the same finishing time
                round_list.append((src, dst, communication_size))
        pair_list.append(round_list)

        # step 3: intra-server allreduce
        non_overlap_ratio = float(Simulator.CONF_DICT['non_overlap_ratio'])
        if server_num > ring_hd_threshold:
            mask = 1
            communication_size = model_size / NIC_num_in_a_server * non_overlap_ratio / 2
            while mask < server_num:
                round = []
                for src in range(0, server_num):
                    dst = src ^ mask
                    for node in range(0, server_num):
                        for k in range(num_partitions):
                            round.append((src * num_partitions + node * NIC_num_in_a_server + k,
                                          dst * num_partitions + node * NIC_num_in_a_server + k,
                                          communication_size))
                pair_list.append(round)
                mask *= 2
                communication_size /= 2
            mask = 1
            communication_size = model_size / NIC_num_in_a_server / server_num * non_overlap_ratio
            while mask < server_num:
                round = []
                for src in range(0, server_num):
                    dst = src ^ mask
                    for node in range(0, server_num):
                        for k in range(num_partitions):
                            round.append((src * num_partitions + node * NIC_num_in_a_server + k,
                                          dst * num_partitions + node * NIC_num_in_a_server + k,
                                          communication_size))
                pair_list.append(round)
                mask *= 2
                communication_size *= 2
        else:
            round_num = server_num - 1
            communication_size = model_size / NIC_num_in_a_server / 2 / server_num * non_overlap_ratio
            for _ in range(2):
                for _ in range(round_num):
                    forward = []
                    backward = []
                    for i in range(server_num):
                        src = i
                        dst = (i + 1) % server_num
                        for j in range(server_num):
                            for k in range(num_partitions):
                                forward.append((src * num_partitions + j * NIC_num_in_a_server + k,
                                                dst * num_partitions + j * NIC_num_in_a_server + k, communication_size))
                                backward.append((dst * num_partitions + j * NIC_num_in_a_server + k,
                                                src * num_partitions + j * NIC_num_in_a_server + k, communication_size))
                    pair_list.append(forward + backward)

        # step 4: inter-server mesh communication
        communication_size = model_size / NIC_num_in_a_server
        round_list = []
        for src_server in range(server_num):
            for dst_server in range(server_num):
                if src_server == dst_server:
                    continue
                for k in range(num_partitions):
                    src = src_server * NIC_num_in_a_server + dst_server * num_partitions + k
                    dst = dst_server * NIC_num_in_a_server + src_server * num_partitions + k
                # other flows have the same finishing time
                round_list.append((src, dst, communication_size))
        pair_list.append(round_list)

        # step 5: allgather for GPUs under every server
        if NIC_num_in_a_server > ring_hd_threshold:
            mask = 1
            communication_size = model_size / NIC_num_in_a_server
            while mask < NIC_num_in_a_server:
                round = []
                for src in range(0, NIC_num_in_a_server):
                    dst = src ^ mask
                    for node in range(0, server_num):
                        round.append((src + node * NIC_num_in_a_server, dst + node * NIC_num_in_a_server, communication_size))
                pair_list.append(round)
                mask *= 2
                communication_size *= 2
        else:
            round_num = NIC_num_in_a_server - 1
            communication_size = model_size / NIC_num_in_a_server / 2
            for _ in range(round_num):
                forward = []
                backward = []
                for i in range(NIC_num_in_a_server):
                    src = i
                    if i == NIC_num_in_a_server - 1:
                        dst = 0
                    else:
                        dst = i + 1
                    for j in range(server_num):
                        forward.append((src + j * NIC_num_in_a_server, dst + j * NIC_num_in_a_server, communication_size))
                        backward.append((dst + j * NIC_num_in_a_server, src + j * NIC_num_in_a_server, communication_size))
                pair_list.append(forward + backward)

        return pair_list

    def get_expected_completion_time(self, task_seq = 0):
        from rapidnetsim.core.simulator import Simulator
        task_list = eval(Simulator.CONF_DICT['task_list'])
        _, model_size, task_occupied_NIC_num = task_list[task_seq]
        NIC_num_in_a_server = int(Simulator.CONF_DICT['NIC_num_in_a_server'])
        non_overlap_ratio = float(Simulator.CONF_DICT['non_overlap_ratio'])
        network_transmission_delay = float(Simulator.CONF_DICT['network_transmission_delay'])
        inserver_transmission_delay = float(Simulator.CONF_DICT['inserver_transmission_delay'])
        server_num = int(task_occupied_NIC_num / NIC_num_in_a_server)
        if task_occupied_NIC_num == 1:
            intra_datafactor = 1
            inter_datafactor = 0
        elif task_occupied_NIC_num <= NIC_num_in_a_server:
            intra_datafactor = 2 * (task_occupied_NIC_num - 1) / task_occupied_NIC_num
            inter_datafactor = 0
        elif task_occupied_NIC_num <= 4 * NIC_num_in_a_server:
            intra_datafactor = 2 * (1 - 1 / NIC_num_in_a_server)
            inter_datafactor = 2 * (1 / NIC_num_in_a_server - 1 / task_occupied_NIC_num)
        else:
            intra_datafactor = 2 * ( 1 - 1 / NIC_num_in_a_server + non_overlap_ratio * (1 / NIC_num_in_a_server - 1 / task_occupied_NIC_num))
            inter_datafactor = 2 / NIC_num_in_a_server
        if task_occupied_NIC_num == 1:
            intra_times = 0
            inter_times = 0
        elif task_occupied_NIC_num <= NIC_num_in_a_server:
            intra_times = 2 * (task_occupied_NIC_num - 1)
            inter_times = 0
        elif task_occupied_NIC_num <= 4 * NIC_num_in_a_server:
            if NIC_num_in_a_server > 8:
                intra_times = 2 * math.log2(NIC_num_in_a_server)
            else:
                intra_times = 4 * (NIC_num_in_a_server - 1)
            inter_times = 2 * (server_num - 1)
        else:
            if NIC_num_in_a_server > 8:
                intra_times = 2 * math.log2(NIC_num_in_a_server)
            else:
                intra_times = 4 * (NIC_num_in_a_server - 1)
            inter_times = 2
            if server_num > 8:
                intra_times += 2 * math.log2(server_num)
            else:
                intra_times += 2 * (server_num - 1)
        expected_completion_time = model_size * (intra_datafactor / float(Simulator.CONF_DICT['inner_server_bandwidth']) + inter_datafactor / float(Simulator.CONF_DICT['switch_port_bandwidth'])) + intra_times * inserver_transmission_delay + inter_times * network_transmission_delay
        return expected_completion_time

if __name__ == '__main__':
    test = HwOxcAllreduceNopeer()
    res = test._get_hw_oxc_allreduce5step_every_round_pair(32, 4, 8)
    # print(res)
