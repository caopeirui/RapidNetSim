



class OutputPort:
    """Express the output port of a device.
    """
    def __init__(self, device_id) -> None:
        self._device_id = device_id
        self._port_target_map = {}    # {port id : target device id}
        self._target_portlist_map = {}    # {target device id: [port id, port id, ...]}

        # port_id is only used to express the map of different targets.
        self._created_max_id = 0


    def __str__(self) -> str:
        print_dict = {
            'device_id': self._device_id,
            'port_target_map': self._port_target_map,
            'target_portlist_map': self._target_portlist_map,
        }
        print_str = '<OutputPort | '
        for key, val in print_dict.items():
            print_str += key + ': ' + str(val) + ', '
        print_str += '>'
        return print_str


    def get_port_list(self, target_device):
        return self._target_portlist_map[target_device]


    def get_target_device_id(self, port_id):
        return self._port_target_map[port_id]


    def use_a_port(self, target_device_id):
        self._port_target_map[self._created_max_id] = target_device_id

        if self._target_portlist_map.get(target_device_id):
            self._target_portlist_map[target_device_id].append(self._created_max_id)
        else:
            self._target_portlist_map[target_device_id] = [self._created_max_id]

        self._created_max_id += 1


    def release_a_port(self, target_device_id):
        port_id = self._target_portlist_map[target_device_id][0]
        del self._port_target_map[port_id]
        del self._target_portlist_map[target_device_id][0]
