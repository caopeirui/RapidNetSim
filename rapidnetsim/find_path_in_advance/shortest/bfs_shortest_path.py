
import math
import queue
import time

class BfsShortestPathStatic:
    LEAF_TO_SPINE_MAP = {}    # {GPUid: spineid}
    LEAF_EGRESS_OCCUPIED = {}    # {leafid: {occupied next_hop_spineid: True, ...}}
    SPINE_TO_LEAF_MAP = {}    # {GPUid: leafid}
    SPINE_EGRESS_OCCUPIED = {}    # {spineid: {occupied next_hop_leafid: True, ...}}


    def __init__(self) -> None:
        raise Exception("BfsShortestPathStatic acts as global static class and should not be instantiated!")
        

    @staticmethod
    def set_path_dict(taskid):
        from rapidnetsim.core.simulator import Simulator
        infra = Simulator.get_infrastructure()
        rapid_graph = infra.get_graph()
        device_path_dict = infra.get_device_path_dict()
        switch_port_bandwidth = float(Simulator.CONF_DICT['switch_port_bandwidth'])

        device_set = rapid_graph.get_vertex_set()

        NIC_num = int(Simulator.CONF_DICT['NIC_num'])
        NIC_set = set([i for i in range(NIC_num)])
        switch_set = device_set ^ NIC_set

        shortest_path_length = BfsShortestPathStatic.get_shortest_path_length(rapid_graph, switch_set)
        start = time.time()
        # Only record switch_set to speed up.
        for src in switch_set:
            for dst in switch_set:
                if src != dst:
                    out_edge_dict = rapid_graph.get_out_edge_dict_from(src)
                    for next_hop_id in out_edge_dict:
                        # Only record switch_set to speed up.
                        if next_hop_id < NIC_num:
                            continue
                        if shortest_path_length[src][dst] == shortest_path_length[next_hop_id][dst] + 1:
                            port_num = int(infra.get_the_links_capacity(src, next_hop_id, taskid) / switch_port_bandwidth)
                            assert(port_num > 0)
                            for _ in range(port_num):
                                device_path_dict[src].add_to_next_hop_dict(dst, next_hop_id, taskid)
        end = time.time()
        print('The elapsed time of recording to_next_hop_dict:', end - start)


    @staticmethod
    def get_shortest_path_length(graph, device_set):
        shortest_path_length = {}
        for src in device_set:
            shortest_path_length[src] = {}
            for dst in device_set:
                shortest_path_length[src][dst] = float("inf")

        start_time = time.time()
        for device_id in device_set:
            shortest_path_length[device_id][device_id] = 0
            bfs_queue = queue.Queue()
            record_gone_dict = {}
            cur_layer = 0
            bfs_queue.put((device_id, cur_layer))

            while bfs_queue.empty() is False:
                tmp_src, cur_layer = bfs_queue.get()
                record_gone_dict[tmp_src] = True
                connect_list = graph.get_out_edge_dict_from(tmp_src)
                for tmp_dst in connect_list:
                    if tmp_dst not in record_gone_dict:
                        shortest_path_length[tmp_src][tmp_dst] = 1
                        shortest_path_length[device_id][tmp_dst] = cur_layer + 1
                        record_gone_dict[tmp_dst] = True
                        bfs_queue.put((tmp_dst, cur_layer + 1))
        consuming_time = time.time() - start_time
        print('Consuming time of calculating shortest path:', consuming_time)
        return shortest_path_length
