
class HwOxcScheduler2:
    def __init__(self, NIC_num_in_a_server, NIC_num) -> None:
        self._NIC_num_in_a_server = NIC_num_in_a_server
        self._NIC_num = NIC_num
        self._server_num = NIC_num_in_a_server

        self._record_occupied_NIC_set = set()
        self._task_NIC_map = dict()    # Record NIC id used by every task.
        self._server_unused_NIC_num_map = dict()    # Record the number of unoccupied NIC belonging to every switch.
        for i in range(0, self._server_num):
            self._server_unused_NIC_num_map[i] = NIC_num_in_a_server


    def schedule(self, task_occupied_NIC_num, taskid, current_time, waiting_task_list):
        from rapidnetsim.core.simulator import Simulator
        allocate_succeed = False
        need_NIC_list = None
        allocated_link_mapping = None
        all_gpu_index = None
        link_mapping = None
        NIC_num_in_a_server = self._NIC_num_in_a_server
        
        unoccpuied_NIC_set = self._get_leisure_NIC_set()

        Simulator.occupied_num_logger.write(f'{Simulator._current_time},{len(unoccpuied_NIC_set)},{taskid},{task_occupied_NIC_num}\n')

        if task_occupied_NIC_num > len(unoccpuied_NIC_set):
            allocate_succeed = False
            return allocate_succeed, need_NIC_list, allocated_link_mapping, all_gpu_index, link_mapping
        elif task_occupied_NIC_num > NIC_num_in_a_server:
            assert(task_occupied_NIC_num % NIC_num_in_a_server == 0)
            need_free_server_num = task_occupied_NIC_num // NIC_num_in_a_server
            candidate_servers = dict()
            for server_id, leisure_num in self._server_unused_NIC_num_map.items():
                if leisure_num == NIC_num_in_a_server:
                    candidate_servers[server_id] = self._get_NIC_list_in_switch(server_id, NIC_num_in_a_server)
                    need_free_server_num -= 1
                if need_free_server_num == 0:
                    break
            if need_free_server_num == 0:
                allocate_succeed = True
                need_NIC_list = []
                for server_id in candidate_servers:
                    need_NIC_list += candidate_servers[server_id]
                    self._server_unused_NIC_num_map[server_id] = 0
                self._task_NIC_map[taskid] = need_NIC_list
                allocated_link_mapping = self._generate_link_mapping(candidate_servers)
                for nic in need_NIC_list:
                    self._record_occupied_NIC_set.add(nic)
                return allocate_succeed, need_NIC_list, allocated_link_mapping, all_gpu_index, link_mapping
            else:
                allocate_succeed = False
                return allocate_succeed, need_NIC_list, allocated_link_mapping, all_gpu_index, link_mapping
        else:
            server_unused_NIC_num_map_list = sorted(self._server_unused_NIC_num_map.items(), key = lambda d:d[1], reverse = False)
            for num_required_servers in {1, 2}:
                num_nics_required_per_server = task_occupied_NIC_num / num_required_servers
                num_servers_chosen = 0
                candidate_servers = dict()
                for server_id, unused_nic_num in server_unused_NIC_num_map_list:
                    if unused_nic_num >= num_nics_required_per_server:
                        num_servers_chosen += 1
                        candidate_servers[server_id] = self._get_NIC_list_in_switch(server_id, num_nics_required_per_server)
                    if num_servers_chosen == num_required_servers:
                        allocate_succeed = True
                        need_NIC_list = []
                        for server_id in candidate_servers:
                            need_NIC_list += candidate_servers[server_id]
                            self._server_unused_NIC_num_map[server_id] -= num_nics_required_per_server
                        self._task_NIC_map[taskid] = need_NIC_list
                        for nic in need_NIC_list:
                            self._record_occupied_NIC_set.add(nic)
                        allocated_link_mapping = []
                        if num_servers_chosen > 1:
                            allocated_link_mapping = self._generate_link_mapping(candidate_servers)
                        
                        return allocate_succeed, need_NIC_list, allocated_link_mapping, all_gpu_index, link_mapping
            
            # allocation failed
            allocate_succeed = False
            return allocate_succeed, need_NIC_list, allocated_link_mapping, all_gpu_index, link_mapping


    def update_finished_job(self, taskid, current_time, waiting_task_list):
        NIC_list = self._task_NIC_map[taskid]
        for NIC_id in NIC_list:
            self._record_occupied_NIC_set.remove(NIC_id)
            self._server_unused_NIC_num_map[NIC_id // self._NIC_num_in_a_server] += 1


    def _get_leisure_NIC_set(self):
        all_NIC_set = set([i for i in range(self._NIC_num)])
        return all_NIC_set ^ self._record_occupied_NIC_set


    def _generate_link_mapping(self, candidate_servers):
        allocated_link_mapping = []
        # We assume that 2^i NICs are chosen in each server, and the number of servers is 2^j
        allocated_num_servers = len(candidate_servers)

        server_ids = []
        allocated_num_NICs_per_server = 0
        for server in candidate_servers:
            server_ids.append(server)
            if allocated_num_NICs_per_server == 0:
                allocated_num_NICs_per_server = len(candidate_servers[server])
            else:
                assert(allocated_num_NICs_per_server == len(candidate_servers[server]))
        assert(allocated_num_servers > 1)
        assert(allocated_num_NICs_per_server > 0)
        # Create links
        threshold = 4
        if allocated_num_servers <= threshold:
            # Use ring for inter-server communication
            for i in range(allocated_num_servers):
                src_server = server_ids[i]
                dst_server = server_ids[(i + 1) % allocated_num_servers]
                for j in range(allocated_num_NICs_per_server):
                    allocated_link_mapping.append(
                        (candidate_servers[src_server][j], candidate_servers[dst_server][j], 1))
        else:
            # Create a uniform mesh for inter-server communication
            assert(allocated_num_NICs_per_server % allocated_num_servers == 0)
            link_num = allocated_num_NICs_per_server // allocated_num_servers
            for src_server in range(allocated_num_servers):
                for dst_server in range(allocated_num_servers):
                    if src_server == dst_server:
                        continue
                    for k in range(link_num):
                        src = candidate_servers[server_ids[src_server]][dst_server * link_num + k]
                        dst = candidate_servers[server_ids[dst_server]][src_server * link_num + k]
                    allocated_link_mapping.append((src, dst, 1))

        return allocated_link_mapping


    def _get_NIC_list_in_switch(self, server_id, need_num):
        NIC_num_in_a_server = self._NIC_num_in_a_server
        if need_num == NIC_num_in_a_server:
            return [i for i in range(server_id * NIC_num_in_a_server, (server_id + 1) * NIC_num_in_a_server)]
        elif need_num < NIC_num_in_a_server:
            leisure_NIC_set = self._get_leisure_NIC_set()
            server_NIC_set = set([i for i in range(server_id * NIC_num_in_a_server, (server_id + 1) * NIC_num_in_a_server)])
            
            can_be_used = server_NIC_set & leisure_NIC_set
            res = []
            for NIC_id in can_be_used:
                res.append(NIC_id)
                need_num -= 1
                if need_num <= 0:
                    break
            return res
        elif need_num > NIC_num_in_a_server:
            print("Bug: _get_NIC_list_in_switch need_num > NIC_num_in_a_server")
            exit()
