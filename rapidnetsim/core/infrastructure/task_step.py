import random

class TaskStep:
    def __init__(self, taskid, stepid, a_flow_size, across_network) -> None:
        """A flow is transmitted over the network.
        Args:
        """
        self._taskid = taskid
        self._stepid = stepid
        self._a_flow_size = a_flow_size
        self._across_network = across_network


    def __str__(self) -> str:
        print_dict = {
            'taskid': self._taskid,
            'stepid': self._stepid,
            'a_flow_size': self._a_flow_size,
        }
        print_str = '<TaskStep | '
        for key, val in print_dict.items():
            print_str += key + ': ' + str(val) + ', '
        print_str += '>'
        return print_str


    def get_taskid(self):
        return self._taskid


    def get_stepid(self):
        return self._stepid
    

    def get_flow_size(self):
        return self._a_flow_size


    def get_expected_finish_time(self):
        from rapidnetsim.core.simulator import Simulator
        unit = 1000000
        switch_port_bandwidth = float(Simulator.CONF_DICT['switch_port_bandwidth']) / unit
        inner_server_bandwidth = float(Simulator.CONF_DICT['inner_server_bandwidth']) / unit
        NIC_num_in_a_server = int(Simulator.CONF_DICT['NIC_num_in_a_server'])

        network_transmission_delay = float(Simulator.CONF_DICT['network_transmission_delay'])
        inserver_transmission_delay = float(Simulator.CONF_DICT['inserver_transmission_delay'])

        transmission_delay = inserver_transmission_delay

        bandwidth = inner_server_bandwidth
        if self._across_network == True:
            bandwidth = switch_port_bandwidth
            transmission_delay = network_transmission_delay
        
        task_step_link_occupy_list = Simulator.get_task_step_link_occupy(self._taskid, self._stepid)
        max_expected_finish_time = 0
        for (src, dst, relative_port) in task_step_link_occupy_list:
            if src == dst or (src // NIC_num_in_a_server == dst // NIC_num_in_a_server):
                expected_finish_time = self._a_flow_size / inner_server_bandwidth + inserver_transmission_delay
                if expected_finish_time > max_expected_finish_time:
                    max_expected_finish_time = expected_finish_time
                continue
            the_link_occupied = Simulator.get_link_occupied_for_tasks(src ,dst, relative_port)

            occupied_num = len(the_link_occupied)

            available_bandwidth = bandwidth / occupied_num
            if available_bandwidth > bandwidth:
                available_bandwidth = bandwidth

            expected_finish_time = self._a_flow_size / available_bandwidth + transmission_delay

            if expected_finish_time > max_expected_finish_time:
                max_expected_finish_time = expected_finish_time
        
        return max_expected_finish_time
