

class Graph:
    """Create network graph, supporting to query node connectivity.
    """
    def __init__(self, connect_info_list) -> None:
        """
        Each element in connect_info_list is (start_node_index, end_node_index, link_num).
        """
        self._vertex_set = set()
        self._edge_weight_dict = {}
        self._in_edge_dict = {}
        self._out_edge_dict = {}

        self._subclos_edge_weight_dict = {}

        for (start_node_index, end_node_index, link_num) in connect_info_list:
            # print(start_node_index, end_node_index, link_num)
            self._vertex_set.add(start_node_index)
            self._vertex_set.add(end_node_index)
            self._edge_weight_dict[(start_node_index, end_node_index)] = link_num
            
            if self._in_edge_dict.get(end_node_index):
                self._in_edge_dict[end_node_index].append(start_node_index)
            else:
                self._in_edge_dict[end_node_index] = [start_node_index]

            if self._out_edge_dict.get(start_node_index):
                self._out_edge_dict[start_node_index].append(end_node_index)
            else:
                self._out_edge_dict[start_node_index] = [end_node_index]


    def refresh_graph_connection_info(self, connect_info_list):
        # self._delta_vertex_set = set()

        # Global Simulator._device_path_dict in previous topologyhas been calculated.
        # So following variables can be reset.
        self._vertex_set = set()
        self._edge_weight_dict = {}
        self._in_edge_dict = {}
        self._out_edge_dict = {}

        self._subclos_edge_weight_dict = {}

        for (start_node_index, end_node_index, link_num) in connect_info_list:
            # print(start_node_index, end_node_index, link_num)
            self._vertex_set.add(start_node_index)
            self._vertex_set.add(end_node_index)

            self._edge_weight_dict[(start_node_index, end_node_index)] = link_num
            
            self._subclos_edge_weight_dict[(start_node_index, end_node_index)] = link_num

            if self._in_edge_dict.get(end_node_index):
                self._in_edge_dict[end_node_index].append(start_node_index)
            else:
                self._in_edge_dict[end_node_index] = [start_node_index]

            if self._out_edge_dict.get(start_node_index):
                self._out_edge_dict[start_node_index].append(end_node_index)
            else:
                self._out_edge_dict[start_node_index] = [end_node_index]



    def get_in_edge_dict(self):
        """Return all vertices that have an edge toward the given vertex.
        """
        return self._in_edge_dict


    def get_out_edge_dict_from(self, vertex_id):
        """Return all vertices that have an edge incoming from the given vertex.
        """
        return self._out_edge_dict.get(vertex_id)


    def get_in_edge_dict_from(self, vertex_id):
        return self._in_edge_dict.get(vertex_id)

    
    def get_edge_weight_dict(self):
        return self._edge_weight_dict
    

    def get_edge_weight_dict_at_pair(self, src, dst):
        return self._edge_weight_dict[(src, dst)]


    def get_vertex_num(self):
        return len(self._vertex_set)

    
    def get_vertex_set(self):
        return self._vertex_set


    def get_vertex_to_vertexset_linknum(self, vertexid, vertex_list):
        num = 0
        for vid in vertex_list:
            link_num = self._subclos_edge_weight_dict.get((vertexid, vid))
            if link_num:
                num += link_num
        
        return num