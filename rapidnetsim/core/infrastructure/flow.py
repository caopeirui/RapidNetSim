

import random

class Flow:
    def __init__(self, flowid, size, start_time, src, dst, remainder_size, last_calculated_time, taskid, stepid, task_occupied_NIC_num, todo = False, use_NIC_list = []) -> None:
        """A flow is transmitted over the network.
        Args:
            - flowid: A flow identification.
            - size: Total size.
            - start_time: Original start time.
            - src: The original source.
            - dst: The final destination.
            - remainder_size: remainder size waiting to be transmit.
            - last_calculated_time: Record last calculated time.
            - taskid: The flow belongs to taskid.
            - stepid: The flow belongs to stepid in taskid.
        """
        self._flowid = flowid
        self._size = size
        self._start_time = start_time
        self._src = src
        self._dst = dst
        self._remainder_size = remainder_size
        self._last_calculated_time = last_calculated_time
        self._taskid = taskid
        self._stepid = stepid
        self._task_occupied_NIC_num = task_occupied_NIC_num
        self._use_NIC_list = use_NIC_list
        from rapidnetsim.core.simulator import Simulator
        self._server_ids, self._server_nic_map, self._absolute_nic_to_relative_indices = Simulator.TASK_FULL_OCS_PREPARE_DICT[taskid]

        self._hop_list = []


        self._in_the_same_server_flag = False

        self._alpha = 0

    def __str__(self) -> str:
        print_dict = {
            'flowid': self._flowid,
            'size': self._size,
            'start_time': self._start_time,
            'src': self._src,
            'dst': self._dst,
            'remainder_size': self._remainder_size,
            'last_calculated_time': self._last_calculated_time,
            'hop_list': self._hop_list,
            'taskid': self._taskid,
            'stepid': self._stepid,
            'in_the_same_server_flag': self._in_the_same_server_flag,
            'task_occupied_NIC_num': self._task_occupied_NIC_num,
        }
        print_str = '<Flow | '
        for key, val in print_dict.items():
            print_str += key + ': ' + str(val) + ', '
        print_str += '>'
        return print_str


    def find_hop_list(self):
        from rapidnetsim.core.simulator import Simulator
        # Deal with GPUs in the same server.
        if Simulator.whether_belong_the_same_server(self._src, self._dst) == True:
            self.set_in_the_same_server()
            return self._hop_list

        hop_list = []
        # Deal with only 1 GPU occupation
        if self._dst == self._src:
            hop_list = [self._dst]
            self._hop_list = hop_list
            return hop_list


        if Simulator.CONF_DICT['joint_scheduler'] == 'mesh_scheduler':
            hop_list = self._get_mesh_apx_clos_hop_list(self._src, self._dst)
            self._hop_list = hop_list
            return hop_list


        if Simulator.CONF_DICT['joint_scheduler'] in ['hw_oxc_all2all', 'hw_oxc_all2all_sz', 'hw_oxc_all2all2', 'hw_oxc_allreduce', 'hw_oxc_hdallreduce', 'hw_oxc_allreduce_nopeer']:
            hop_list = self._get_hw_oxc_hop_list(self._src, self._dst)
            self._hop_list = hop_list
            return hop_list

        infra = Simulator.get_infrastructure()
        # device_path_dict records the next hop after set path dict.
        device_path_dict = infra.get_device_path_dict()

        # Find subsequent paths.
        find_next_hop_method = Simulator.CONF_DICT['find_next_hop_method']
        assert find_next_hop_method in ['random', 'conservative', 'static_routing', 'static_routing2']

        assert(len(device_path_dict[self._src].get_connected_to_list()) == 1)
        assert(len(device_path_dict[self._dst].get_connected_to_list()) == 1)
        src_ToR = device_path_dict[self._src].get_connected_to_list()[0]
        dst_ToR = device_path_dict[self._dst].get_connected_to_list()[0]

        next_hop = src_ToR
        tmp_src = src_ToR
        hop_list.append((next_hop, 0))

        while next_hop != dst_ToR:
            next_hop_dict = device_path_dict[tmp_src].get_to_next_hop_dict(self._taskid)
            to_dst_next_hop_list = next_hop_dict[dst_ToR]
            
            # Destination based path dict
            if find_next_hop_method == 'random':
                next_hop, relative_port = self._get_random_path(tmp_src, to_dst_next_hop_list, hop_list)
            elif find_next_hop_method == 'static_routing':
                next_hop, relative_port = self._get_static_routing_path(tmp_src, to_dst_next_hop_list, hop_list, self._src)
            elif find_next_hop_method == 'static_routing2':
                next_hop, relative_port = self._get_static_routing2_path(tmp_src, to_dst_next_hop_list, hop_list, self._src)

            hop_list.append((next_hop, relative_port))

            # Update next-hop tmp_src
            tmp_src = next_hop
        
        hop_list.append((self._dst, 0))
        self._hop_list = hop_list


    def _get_mesh_apx_clos_hop_list(self, src, dst):
        from rapidnetsim.core.simulator import Simulator
        # NIC_num = int(Simulator.CONF_DICT['NIC_num'))
        # leaf_switch_num = int(Simulator.CONF_DICT['leaf_switch_num'))
        downlinks = int(Simulator.CONF_DICT['downlinks'])

        # infra = Simulator.get_infrastructure()

        src_switch = Simulator.get_scheduler().belong_which_leaf_switch(src)
        dst_switch = Simulator.get_scheduler().belong_which_leaf_switch(dst)
        if src_switch == dst_switch:
            return [src_switch, dst]
        
        switch_list = Simulator.TASK_SWITCH_DICT[self._taskid]
        if len(switch_list) == 2:
            return [src_switch, dst_switch, dst]

        virtual_clos_leaf_spine_link_num = downlinks / (self._task_occupied_NIC_num / downlinks)
        
        switch_group_map = {}
        cnt = 0
        for swith_id in switch_list:
            switch_group_map[swith_id] = cnt
            cnt += 1

        src_switch_group = switch_group_map[src_switch]
        src_group = src % downlinks // virtual_clos_leaf_spine_link_num
        dst_switch_group = switch_group_map[dst_switch]
        # dst_group = dst % downlinks // virtual_clos_leaf_spine_link_num
        
        if src_group == src_switch_group:
            return [src_switch, dst_switch, dst]
        else:
            if src_group == dst_switch_group:
                return [src_switch, dst_switch, dst]
            else:
                for mid_switch, mid_switch_group in switch_group_map.items():
                    if mid_switch_group == src_group:
                        return [src_switch, mid_switch, dst_switch, dst]



    def _get_hw_oxc_hop_list(self, src, dst):
        server_ids = self._server_ids
        server_nic_map = self._server_nic_map
        absolute_nic_to_relative_indices = self._absolute_nic_to_relative_indices

        server_num = len(server_ids)
        num_nics_per_server = len(server_nic_map[server_ids[0]])
        threshold = 4

        if absolute_nic_to_relative_indices[src][0] == absolute_nic_to_relative_indices[dst][0]:
            # src and dst are in the same server
            return [(dst, 0)]
        elif server_num <= threshold:
            src_server_id, src_nic_serial = absolute_nic_to_relative_indices[src]
            dst_server_id, dst_nic_serial = absolute_nic_to_relative_indices[dst]

            if dst_server_id == (src_server_id + 1) % server_num:
                if src_nic_serial == dst_nic_serial:
                    return [(dst, 0)]
                else:
                    dst_mid = server_nic_map[server_ids[dst_server_id]][src_nic_serial]
                    return [(dst_mid, 0), (dst, 0)]
            else:
                print('debug: No link from src server to dst server')
                print('debug nolink flow', self)
                exit()
        else:
            src_server_id, src_nic_serial = absolute_nic_to_relative_indices[src]
            dst_server_id, dst_nic_serial = absolute_nic_to_relative_indices[dst]
            assert(num_nics_per_server % server_num == 0)
            link_num = num_nics_per_server // server_num
            # there are multiple links between the two servers
            src_mid_nic_serial = link_num * dst_server_id + (src_nic_serial % link_num)
            dst_mid_nic_serial = link_num * src_server_id + (src_nic_serial % link_num)
            src_mid = server_nic_map[server_ids[src_server_id]][src_mid_nic_serial]
            dst_mid = server_nic_map[server_ids[dst_server_id]][dst_mid_nic_serial]
            hop_list = []
            if src != src_mid:
                hop_list += [(src_mid, 0)]
            hop_list += [(dst_mid, 0)]
            if dst_mid != dst:
                hop_list += [(dst, 0)]
            return hop_list


    def _get_random_path(self, tmp_src, to_dst_next_hop_list, hop_list):
        # Approximate ECMP
        # Currently, if every NIC has multiple shortest paths to another NIC,
        # we select a shortest path randomly.
        while True:
            rdm = random.randint(0, len(to_dst_next_hop_list) - 1)
            next_hop = to_dst_next_hop_list[rdm]
            if next_hop not in hop_list:
                # Avoid repeat loop paths.
                break
        
        absolute_index = rdm
        selected_switch_port_list = []
        for i, switch_id in enumerate(to_dst_next_hop_list):
            if switch_id == next_hop:
                selected_switch_port_list.append(i)
        relative_port = selected_switch_port_list.index(absolute_index)
        return next_hop, relative_port


    def _get_static_routing_path(self, cur_src, to_dst_next_hop_list, hop_list, original_src):
        available_switch_list = []
        for next_hop in to_dst_next_hop_list:
            if next_hop in hop_list:
                # Avoid repeat loop paths.
                continue
            
            available_switch_list.append(next_hop)
        
        available_port_num = len(available_switch_list)
        absolute_index = original_src % available_port_num
        selected_switch = available_switch_list[absolute_index]

        selected_switch_port_list = []
        for i, switch_id in enumerate(available_switch_list):
            if switch_id == selected_switch:
                selected_switch_port_list.append(i)
        relative_port = selected_switch_port_list.index(absolute_index)
        return selected_switch, relative_port


    def _get_static_routing2_path(self, cur_src, to_dst_next_hop_list, hop_list, original_src):
        available_switch_list = []
        for next_hop in to_dst_next_hop_list:
            if next_hop in hop_list:
                # Avoid repeat loop paths.
                continue
            
            available_switch_list.append(next_hop)
        
        available_port_num = len(available_switch_list)
        absolute_index = original_src % available_port_num
        selected_switch = available_switch_list[absolute_index]

        selected_switch_port_list = []
        for i, switch_id in enumerate(available_switch_list):
            if switch_id == selected_switch:
                selected_switch_port_list.append(i)
        # relative_port = selected_switch_port_list.index(absolute_index)
        relative_port = original_src # tmp test
        return selected_switch, relative_port


    def get_hop_list(self):
        """Get the path from src to dst.
        All the elements are feasible next hop.
        The last element in hop_list is dst.
        """
        return self._hop_list


    def set_hop_list(self, hop_list):
        self._hop_list = hop_list


    def get_flowid(self):
        return self._flowid

    
    def get_last_calculated_time(self):
        return self._last_calculated_time


    def set_last_calculated_time(self, sim_time):
        self._last_calculated_time = sim_time


    def set_remainder_size(self, remainder_size):
        self._remainder_size = remainder_size
    

    def get_remainder_size(self):
        return self._remainder_size


    def set_start_time(self, start_time):
        self._start_time = start_time


    def get_start_time(self):
        return self._start_time


    def get_src(self):
        return self._src


    def get_dst(self):
        return self._dst

    
    def get_size(self):
        return self._size


    def get_taskid(self):
        return self._taskid


    def get_stepid(self):
        return self._stepid


    def set_in_the_same_server(self):
        self._in_the_same_server_flag = True


    def is_in_the_same_server(self):
        return self._in_the_same_server_flag

