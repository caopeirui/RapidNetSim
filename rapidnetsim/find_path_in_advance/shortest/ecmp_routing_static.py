


class EcmpRoutingStatic:

    def __init__(self) -> None:
        raise Exception("EcmpRoutingStatic acts as global static class and should not be instantiated!")
        

    @staticmethod
    def set_path_dict():
        from rapidnetsim.core.simulator import Simulator
        rapid_graph = Simulator.get_infrastructure().get_graph()

        device_path_dict = Simulator.get_infrastructure().get_device_path_dict()

        device_num = rapid_graph.get_vertex_num()

        shortest_path_length = EcmpRoutingStatic.get_shortest_path_length(rapid_graph)

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
        shortest_path_length = [[None for i in range(device_num)] for i in range(device_num)]
        
        # Initial scan to find easy shortest paths.
        for src in range(device_num):
            for dst in range(device_num):
                if src == dst:
                    shortest_path_length[src][dst] = 0
                elif dst in graph.get_out_edge_dict_from(src):
                    shortest_path_length[src][dst] = 1
                else:
                    shortest_path_length[src][dst] = float("inf")
        
        # When device_num = 2048, The two-layer loop takes 2.5 seconds,
        # so Floyd-Warshall algorithm takes 2048 * 2.5 seconds.
        # Floyd-Warshall algorithm.
        for mid in range(device_num):
            for src in range(device_num):
                for dst in range(device_num):
                    if shortest_path_length[src][dst] > shortest_path_length[src][mid] + shortest_path_length[mid][dst]:
                        shortest_path_length[src][dst] = shortest_path_length[src][mid] + shortest_path_length[mid][dst]
        return shortest_path_length
