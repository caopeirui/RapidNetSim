

class HwOxcScheduler:
    def __init__(self, NIC_num_in_a_server, NIC_num) -> None:
        self._NIC_num_in_a_server = NIC_num_in_a_server
        self._NIC_num = NIC_num

        self._record_occupied_NIC_set = set()
        self._task_NIC_map = dict()    # Record NIC id used by every task.
        self._switch_leisure_NIC_num_map = dict()    # Record the number of unoccupied NIC belonging to every switch.
        self._server_num = NIC_num_in_a_server
        for i in range(NIC_num, NIC_num + self._server_num):
            self._switch_leisure_NIC_num_map[i] = NIC_num_in_a_server


    def schedule(self, task_occupied_NIC_num, taskid, current_time, waiting_task_list):
        from rapidnetsim.core.simulator import Simulator
        allocate_succeed = False
        need_NIC_list = None
        allocated_link_mapping = None
        all_gpu_index = None
        link_mapping = None
        NIC_num_in_a_server = self._NIC_num_in_a_server
        
        unoccpuied_NIC_set = self._get_leisure_NIC_set()

        if task_occupied_NIC_num == self._NIC_num and len(unoccpuied_NIC_set) == task_occupied_NIC_num:
            allocated_link_mapping = []
            need_NIC_list = [i for i in range(self._NIC_num)]
            allocate_succeed = True
            self._task_NIC_map[taskid] = need_NIC_list
            for src in need_NIC_list:
                src_belong = src // NIC_num_in_a_server
                src_port_serial = src % NIC_num_in_a_server
                dst = NIC_num_in_a_server * src_port_serial + src_belong
                allocated_link_mapping.append((src, dst, 1))
                self._record_occupied_NIC_set.add(src)
            for i in range(self._NIC_num, self._NIC_num + NIC_num_in_a_server):
                self._switch_leisure_NIC_num_map[i] = 0

            return allocate_succeed, need_NIC_list, allocated_link_mapping, all_gpu_index, link_mapping

        if task_occupied_NIC_num > len(unoccpuied_NIC_set):
            allocate_succeed = False
        else:
            need_NIC_list = None
            need_free_switch_num = int(task_occupied_NIC_num / NIC_num_in_a_server)
            tmp_NIC_record = []
            residual_need_num = task_occupied_NIC_num
            if task_occupied_NIC_num >= NIC_num_in_a_server:
                #  Preferentially assign NICs to the full-free switch.
                for switch_id, leisure_num in self._switch_leisure_NIC_num_map.items():
                    if leisure_num == NIC_num_in_a_server:
                        tmp_NIC_record += self._get_NIC_list_in_switch(switch_id, NIC_num_in_a_server, self._NIC_num, NIC_num_in_a_server)
                        self._switch_leisure_NIC_num_map[switch_id] -= NIC_num_in_a_server
                        need_free_switch_num -= 1
                        residual_need_num -= NIC_num_in_a_server
                    if need_free_switch_num == 0:
                        break
            # task_occupied_NIC_num < NIC_num_in_a_server
            else:
                # Reversely sort by NIC_num.
                switch_leisure_NIC_num_map_list = sorted(self._switch_leisure_NIC_num_map.items(), key = lambda d:d[1], reverse = True)
                # Preferentially assign NICs to the one switch.
                # Meanwhile do not waste full-free switches.
                if residual_need_num > 0:
                    for (switch_id, leisure_num) in switch_leisure_NIC_num_map_list:
                        if leisure_num < NIC_num_in_a_server and leisure_num > residual_need_num:
                            tmp_NIC_record += self._get_NIC_list_in_switch(switch_id, NIC_num_in_a_server, self._NIC_num, residual_need_num)
                            self._switch_leisure_NIC_num_map[switch_id] -= residual_need_num
                            residual_need_num = 0
                            break

                    if residual_need_num > 0:
                        for (switch_id, leisure_num) in switch_leisure_NIC_num_map_list:
                            if leisure_num == NIC_num_in_a_server:
                                self._switch_leisure_NIC_num_map[switch_id] -= residual_need_num
                                tmp_NIC_record += self._get_NIC_list_in_switch(switch_id, NIC_num_in_a_server, self._NIC_num, residual_need_num)
                                residual_need_num = 0
                                break
                    
                    if residual_need_num > 0:
                        for (switch_id, leisure_num) in switch_leisure_NIC_num_map_list:
                            self._switch_leisure_NIC_num_map[switch_id] -= leisure_num
                            tmp_NIC_record += self._get_NIC_list_in_switch(switch_id, NIC_num_in_a_server, self._NIC_num, leisure_num)
                            residual_need_num -= leisure_num

            
            if residual_need_num == 0:
                need_NIC_list = tmp_NIC_record
            else:
                # Cannot allocate a new task. Rollback!
                for NIC_id in tmp_NIC_record:
                    self._switch_leisure_NIC_num_map[self.belong_which_leaf_switch(NIC_id)] += 1
                allocate_succeed = False
                return allocate_succeed, need_NIC_list, allocated_link_mapping, all_gpu_index, link_mapping


            self._task_NIC_map[taskid] = need_NIC_list
            allocated_link_mapping = []

            leaf_switch_list = []
            switch_NIC_cnt = {}
            for NIC_id in need_NIC_list:
                switch_id = self.belong_which_leaf_switch(NIC_id)
                if switch_NIC_cnt.get(switch_id):
                    switch_NIC_cnt[switch_id] += 1
                else:
                    switch_NIC_cnt[switch_id] = 1

                leaf_switch_list.append(switch_id)
                # Links between NICs and leaf switches.
                # allocated_link_mapping.append((NIC_id, switch_id, 2))
                # allocated_link_mapping.append((switch_id, NIC_id, 2))

                # self._record_occupied_NIC_set.add(NIC_id)


            leaf_switch_set = set(leaf_switch_list)
            leaf_switch_list = sorted(list(leaf_switch_set))
            switch_num = len(leaf_switch_list)
            
            if switch_num == 2:
                pass
                # allocated_link_mapping.append((leaf_switch_list[0], leaf_switch_list[1], NIC_num_in_a_server))
                # allocated_link_mapping.append((leaf_switch_list[1], leaf_switch_list[0], NIC_num_in_a_server))
            elif switch_num > 2:
                for i in range(switch_num):
                    src = leaf_switch_list[i]
                    if i == switch_num - 1:
                        dst = leaf_switch_list[0]
                    else:
                        dst = leaf_switch_list[i + 1]
                    # allocated_link_mapping.append((src, dst, NIC_num_in_a_server))
                    # allocated_link_mapping.append((dst, src, NIC_num_in_a_server))
            allocate_succeed = True
            # Simulator.TASK_SWITCH_DICT[taskid] = leaf_switch_list
            # Simulator.TASK_NIC_DICT[taskid] = need_NIC_list

            # ---- Actually effect allocated_link_mapping -----
            # Detect the number of occupied servers.
            # Regular linking
            for src in need_NIC_list:
                src_belong = src // NIC_num_in_a_server
                src_port_serial = src % NIC_num_in_a_server
                dst = NIC_num_in_a_server * src_port_serial + src_belong
                link_num = NIC_num_in_a_server / (task_occupied_NIC_num / NIC_num_in_a_server) if NIC_num_in_a_server / (task_occupied_NIC_num / NIC_num_in_a_server) > 1 else 1
                allocated_link_mapping.append((src, dst, link_num))
                self._record_occupied_NIC_set.add(src)
        return allocate_succeed, need_NIC_list, allocated_link_mapping, all_gpu_index, link_mapping


    def update_finished_job(self, taskid, current_time, waiting_task_list):
        NIC_list = self._task_NIC_map[taskid]
        for NIC_id in NIC_list:
            self._record_occupied_NIC_set.remove(NIC_id)
            self._switch_leisure_NIC_num_map[self.belong_which_leaf_switch(NIC_id)] += 1


    def belong_which_leaf_switch(self, NIC_id):
        return NIC_id // self._NIC_num_in_a_server + self._NIC_num


    def _get_leisure_NIC_set(self):
        all_NIC_set = set([i for i in range(self._NIC_num)])
        return all_NIC_set ^ self._record_occupied_NIC_set


    def _get_NIC_list_in_switch(self, switch_id, NIC_num_in_a_server, NIC_num, need_num):
        if need_num == NIC_num_in_a_server:
            return [i for i in range((switch_id - NIC_num) * NIC_num_in_a_server, (switch_id - NIC_num + 1) * NIC_num_in_a_server)]
        elif need_num < NIC_num_in_a_server:
            leisure_NIC_set = self._get_leisure_NIC_set()
            switch_NIC_set = set([i for i in range((switch_id - NIC_num) * NIC_num_in_a_server, (switch_id - NIC_num + 1) * NIC_num_in_a_server)])
            
            can_be_used = switch_NIC_set & leisure_NIC_set
            res = []
            for NIC_id in can_be_used:
                res.append(NIC_id)
                need_num -= 1
                if need_num <= 0:
                    break
            return res
        elif need_num > NIC_num_in_a_server:
            print("Bug: _get_NIC_list_in_switch need_num > NIC_num_in_a_server")
            return