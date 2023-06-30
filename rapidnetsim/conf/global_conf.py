

class GlobalConf:
    def __init__(self, config_handler) -> None:
        self._config_handler = config_handler
    

    def get_parameter(self, key):
        return self._config_handler['Parameter'][key]


    def get_topo_type(self):
        topo_type = self._config_handler['Topology']['topo_type']
        return topo_type
      

    def get_connect_info_list(self):
        """
        The ID of NIC starts from 0.
        The ID of switch starts from the maximum NIC ID + 1.
        (src_id, dst_id, link_num)
        """
        connect_info_list_str = self._config_handler['Topology']['connect_info_list']
        connect_info_list = eval(connect_info_list_str)
        return connect_info_list


    def get_task_info(self, key):
        return self._config_handler['Task'][key]