

from rapidnetsim.core.infrastructure.port import OutputPort
class Device:
    """Provide to record next hop info for every device including NIC and switch.
    """
    def __init__(self, index) -> None:
        self._index = index

        self._connected_to_list = []

        # _to_next_hop_dict Records the next hop when flow arrives every device.
        # key: destination id, value: next switch list.
        self._to_next_hop_dict = {}

        self._port = OutputPort(index)

        self._nic_spine_map = None


    def __str__(self) -> str:
        print_dict = {
            'index': self._index,
            'connected_to_list': self._connected_to_list,
            'to_next_hop_dict': self._to_next_hop_dict,
            'port': self._port,
        }
        print_str = '<Device | '
        for key, val in print_dict.items():
            print_str += key + ': ' + str(val) + ', '
        print_str += '>'
        return print_str


    def get_index(self):
        return self._index


    def add_connect(self, dst, link_num):
        if dst in self._connected_to_list:
            # raise Exception(f"Target device {dst} is already connected from device {self.get_index()}")
            # print(f"Target device {dst} is already connected from device {self.get_index()}")
            pass
        else:
            self._connected_to_list.append(dst)

        # Modify port info
        # self._port.use_a_port(dst)


    def del_connect(self, dst):
        # self._connected_to_list.remove(dst)    # TODO: debug and delete
        # Modify port info
        # self._port.release_a_port(dst)
        pass


    def has_connect(self, target_id):
        if target_id in self._connected_to_list:
            return True
        else:
            return False


    def add_to_next_hop_dict(self, dst_id, next_hop_id, taskid):
        if not self.has_connect(next_hop_id):
            raise Exception(f"{self} Cannot add a hop to {next_hop_id}, which is not connected.")

        if taskid not in self._to_next_hop_dict:
            self._to_next_hop_dict[taskid] = {}

        if self._to_next_hop_dict[taskid].get(dst_id):
            if next_hop_id in self._to_next_hop_dict[taskid].get(dst_id):
                # raise Exception(f"Duplicate add {next_hop_id} in _to_next_hop_dict.")
                # print(f"Duplicate add {next_hop_id} in _to_next_hop_dict.")
                return

        if self._to_next_hop_dict[taskid].get(dst_id):
            self._to_next_hop_dict[taskid][dst_id].append(next_hop_id)
        else:
            self._to_next_hop_dict[taskid][dst_id] = [next_hop_id]


    def clear_to_next_hop_dict(self, taskid):
        """Call when oxc reconfiguration.
        """
        self._to_next_hop_dict[taskid] = {}


    def get_connected_to_list(self):
        return self._connected_to_list


    def get_to_next_hop_dict(self, taskid):
        if taskid not in self._to_next_hop_dict:
            # -2 means no reconfiguration
            return self._to_next_hop_dict[-2]
        return self._to_next_hop_dict[taskid]


    def set_to_spine_id(self, spine_id):
        self._nic_spine_map = spine_id


    def get_to_spine_id(self):
        return self._nic_spine_map


    def get_port_list(self, target_device):
        """
        Return: [port id, port id, ...] connected to target_device
        """
        return self._port.get_port_list(target_device)


    def get_target_device_id(self, port_id):
        """
        Return: target device id
        """
        return self._port.get_target_device_id(port_id)
