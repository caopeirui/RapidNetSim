

import threading

class MultithreadedEcmpRoutingStatic:

    def __init__(self) -> None:
        raise Exception("EcmpRoutingStatic acts as global static class and should not be instantiated!")
        

    @staticmethod
    def set_path_dict():
        from rapidnetsim.core.simulator import Simulator
        rapid_graph = Simulator.get_infrastructure().get_graph()

        device_path_dict = Simulator.get_infrastructure().get_device_path_dict()

        device_num = rapid_graph.get_vertex_num()

        shortest_path_length = MultithreadedEcmpRoutingStatic.get_shortest_path_length(rapid_graph)
        
        for src in range(device_num):
            for dst in range(device_num):
                if src != dst:
                    out_edge_dict = rapid_graph.get_out_edge_dict_from(src)
                    for next_hop_id in out_edge_dict:
                        if shortest_path_length[src][dst] == shortest_path_length[next_hop_id][dst] + 1:
                            device_path_dict[src].add_to_next_hop_dict(dst, next_hop_id)


    @staticmethod
    def get_shortest_path_length(graph):
        device_num = graph.get_vertex_num()
        MultithreadedEcmpRoutingStatic._shortest_path_length = [[None for i in range(device_num)] for i in range(device_num)]

        # Initial scan to find easy shortest paths.
        for src in range(device_num):
            for dst in range(device_num):
                if src == dst:
                    MultithreadedEcmpRoutingStatic._shortest_path_length[src][dst] = 0
                elif dst in graph.get_out_edge_dict_from(src):
                    MultithreadedEcmpRoutingStatic._shortest_path_length[src][dst] = 1
                else:
                    MultithreadedEcmpRoutingStatic._shortest_path_length[src][dst] = float("inf")
        

        # Make it multithreaded to time efficiency
        # Floyd-Warshall algorithm.
        calc_thread_list = []
        for mid in range(device_num):
            calc_t = threading.Thread(target = MultithreadedEcmpRoutingStatic.calc_mid_device, args = (mid, device_num))
            calc_t.start()
            calc_thread_list.append(calc_t)

        for calc_t in calc_thread_list:
            calc_t.join()

        return MultithreadedEcmpRoutingStatic._shortest_path_length


    @staticmethod
    def calc_mid_device(mid, device_num):
        print('mid', mid)
        for src in range(device_num):
            for dst in range(device_num):
                if MultithreadedEcmpRoutingStatic._shortest_path_length[src][dst] > MultithreadedEcmpRoutingStatic._shortest_path_length[src][mid] + MultithreadedEcmpRoutingStatic._shortest_path_length[mid][dst]:
                    MultithreadedEcmpRoutingStatic._shortest_path_length[src][dst] = MultithreadedEcmpRoutingStatic._shortest_path_length[src][mid] + MultithreadedEcmpRoutingStatic._shortest_path_length[mid][dst]
        print(f'mid {mid} done')
