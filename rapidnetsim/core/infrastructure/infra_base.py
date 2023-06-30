
from rapidnetsim.core.infrastructure.device import Device
from rapidnetsim.core.infrastructure.graph import Graph
from rapidnetsim.find_path_in_advance.shortest.bfs_shortest_path import BfsShortestPathStatic


class InfraBase:
    """Create network infrastructure according to selectors and configs.
    """
    def __init__(self) -> None:
        self._graph = None
        self._link_capacity_dict = {}             # {(src, dst): capacity}
        self._link_flow_occupy_dict = {}          # {(src, dst): [flowid, flowid, ...]}
        self._flow_infly_info_dict = {}           # {flowid: Flow}
        self._device_path_dict = {}            # {device_id: Device} records the next hop when flow arrives every device.


    def create_topology(self, connect_info_list):

        self._graph = Graph(connect_info_list)

        self.set_init_link_capacity_and_occupied()

        vertex_set = self._graph.get_vertex_set()
        for index in vertex_set:
            self._device_path_dict[index] = Device(index)
        
        for (start_node_index, end_node_index, link_num) in connect_info_list:
            self.create_connection(start_node_index, end_node_index, link_num)


    def create_connection(self, src, dst, link_num):
        device_src = self._device_path_dict[src]
        device_src.add_connect(dst, link_num)


    def find_all_path(self, taskid):
        from rapidnetsim.core.simulator import Simulator
        find_path_method = Simulator.CONF_DICT['find_path_method']
        if find_path_method == 'shortest':
            BfsShortestPathStatic.set_path_dict(taskid)


    def refresh_link_flow_occupy_dict(self):
        self._link_flow_occupy_dict= {}


    def reconfigure_topo(self, delta_connect_info_list, taskid):
        """Reconfigure topology
        """
        self._graph.refresh_graph_connection_info(delta_connect_info_list)

        # Reconfiguration according to taskid
        self.set_link_capacity(taskid)

        vertex_set = self._graph.get_vertex_set()
        for index in vertex_set:
            if not self._device_path_dict.get(index):
                self._device_path_dict[index] = Device(index)
            else:
                self._device_path_dict[index].clear_to_next_hop_dict(taskid)

        for (start_node_index, end_node_index, link_num) in delta_connect_info_list:
            self.create_connection(start_node_index, end_node_index, link_num)


    def get_device_path_dict(self):
        """Return device_path_dict which records the next hop when flow arrives every device.
        """
        return self._device_path_dict

    
    def get_device(self, device_id):
        return self._device_path_dict[device_id]


    def get_graph(self):
        return self._graph


    def set_init_link_capacity_and_occupied(self):
        from rapidnetsim.core.simulator import Simulator
        switch_port_bandwidth = float(Simulator.CONF_DICT['switch_port_bandwidth'])
        edge_weight_dict = self._graph.get_edge_weight_dict()
        self._link_capacity_dict[-2] = {}
        self._link_flow_occupy_dict[-2] = {}
        for (src, dst), weight in edge_weight_dict.items():
            # -2 means no reconfiguration
            self._link_capacity_dict[-2][(src, dst)] = weight * switch_port_bandwidth
            self._link_flow_occupy_dict[-2][(src, dst)] = []



    def set_link_capacity(self, taskid):
        from rapidnetsim.core.simulator import Simulator
        switch_port_bandwidth = float(Simulator.CONF_DICT['switch_port_bandwidth'])
        edge_weight_dict = self._graph.get_edge_weight_dict()

        if taskid not in self._link_capacity_dict:
            self._link_capacity_dict[taskid] = {}

        for (src, dst), weight in edge_weight_dict.items():
            self._link_capacity_dict[taskid][(src, dst)] = weight * switch_port_bandwidth


    def get_link_capacity_dict(self, taskid):
        if taskid not in self._link_capacity_dict:
            # -2 means no reconfiguration
            return self._link_capacity_dict[-2]
        return self._link_capacity_dict[taskid]


    def get_the_links_capacity(self, src, dst, taskid):
        if taskid not in self._link_capacity_dict:
            # -2 means no reconfiguration
            return self._link_capacity_dict[-2][(src, dst)]
        # tmp debug
        if not self._link_capacity_dict[taskid].get((src, dst)):
            from rapidnetsim.core.simulator import Simulator
            return float(Simulator.CONF_DICT['switch_port_bandwidth'])
        return self._link_capacity_dict[taskid][(src, dst)]

