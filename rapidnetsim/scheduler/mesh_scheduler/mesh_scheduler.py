import math

class MeshScheduler:
    def __init__(self, leaf_switch_num, leaf_switch_port_num, downlinks, NIC_num) -> None:
        self._leaf_switch_num = leaf_switch_num
        self._leaf_switch_port_num = leaf_switch_port_num
        self._downlinks = downlinks
        self._NIC_num = NIC_num

        self._record_occupied_NIC_set = set()
        self._task_NIC_map = dict()    # Record NIC id used by every task.
        self._switch_leisure_NIC_num_map = dict()    # Record the number of unoccupied NIC belonging to every switch.
        for i in range(NIC_num, NIC_num + leaf_switch_num):
            self._switch_leisure_NIC_num_map[i] = self._downlinks


    def schedule(self, task_occupied_NIC_num, taskid, current_time, waiting_task_list):
        from rapidnetsim.core.simulator import Simulator
        allocate_succeed = False
        need_NIC_list = None
        allocated_link_mapping = None
        all_gpu_index = None
        link_mapping = None
        downlinks = self._downlinks

        unoccpuied_NIC_set = self._get_leisure_NIC_set()

        if task_occupied_NIC_num > len(unoccpuied_NIC_set):
            allocate_succeed = False
        else:
            need_NIC_list = None
            need_free_witch_num = int(task_occupied_NIC_num / downlinks)
            tmp_NIC_record = []
            residual_need_num = task_occupied_NIC_num
            if task_occupied_NIC_num >= downlinks:
                #  Preferentially assign NICs to the full-free switch.
                for switch_id, leisure_num in self._switch_leisure_NIC_num_map.items():
                    if leisure_num == downlinks:
                        tmp_NIC_record += self._get_NIC_list_in_switch(switch_id, downlinks, self._NIC_num, downlinks)
                        self._switch_leisure_NIC_num_map[switch_id] -= downlinks
                        need_free_witch_num -= 1
                        residual_need_num -= downlinks
                    if need_free_witch_num == 0:
                        break
                
                # After big tasks fill fragmentization, the result is getting worse. 
                # if residual_need_num > 0:
                #     # Reversely sort by NIC_num
                #     switch_leisure_NIC_num_map_list = sorted(self._switch_leisure_NIC_num_map.items(), key = lambda d:d[1], reverse = True)
                #     for (switch_id, leisure_num) in switch_leisure_NIC_num_map_list:
                #         if residual_need_num <= leisure_num:
                #             self._switch_leisure_NIC_num_map[switch_id] -= residual_need_num
                #             tmp_NIC_record += self._get_NIC_list_in_switch(switch_id, downlinks, self._NIC_num, residual_need_num)
                #             residual_need_num = 0
                #             break
                #         else:
                #             self._switch_leisure_NIC_num_map[switch_id] -= leisure_num
                #             tmp_NIC_record += self._get_NIC_list_in_switch(switch_id, downlinks, self._NIC_num, leisure_num)
                #             residual_need_num -= leisure_num
            
            # task_occupied_NIC_num < downlinks
            else:
                # Reversely sort by NIC_num.
                switch_leisure_NIC_num_map_list = sorted(self._switch_leisure_NIC_num_map.items(), key = lambda d:d[1], reverse = True)
                # Preferentially assign NICs to the one switch.
                # Meanwhile do not waste full-free switches.

                # --- tmp debug: worse situation  ---
                # if residual_need_num <= self._downlinks:
                #     for i in range(len(switch_leisure_NIC_num_map_list) - 1, -1, -1):
                #         if switch_leisure_NIC_num_map_list[i][1] == residual_need_num:
                #             switch_id = switch_leisure_NIC_num_map_list[i][0]
                #             tmp_NIC_record += self._get_NIC_list_in_switch(switch_id, downlinks, self._NIC_num, residual_need_num)
                #             self._switch_leisure_NIC_num_map[switch_id] -= residual_need_num
                #             residual_need_num = 0
                #             break
                # ------
                if residual_need_num > 0:
                    for (switch_id, leisure_num) in switch_leisure_NIC_num_map_list:
                        if leisure_num < downlinks and leisure_num > residual_need_num:
                            tmp_NIC_record += self._get_NIC_list_in_switch(switch_id, downlinks, self._NIC_num, residual_need_num)
                            self._switch_leisure_NIC_num_map[switch_id] -= residual_need_num
                            residual_need_num = 0
                            break

                    if residual_need_num > 0:
                        for (switch_id, leisure_num) in switch_leisure_NIC_num_map_list:
                            if leisure_num == downlinks:
                                self._switch_leisure_NIC_num_map[switch_id] -= residual_need_num
                                tmp_NIC_record += self._get_NIC_list_in_switch(switch_id, downlinks, self._NIC_num, residual_need_num)
                                residual_need_num = 0
                                break
                    
                    if residual_need_num > 0:
                        for (switch_id, leisure_num) in switch_leisure_NIC_num_map_list:
                            self._switch_leisure_NIC_num_map[switch_id] -= leisure_num
                            tmp_NIC_record += self._get_NIC_list_in_switch(switch_id, downlinks, self._NIC_num, leisure_num)
                            residual_need_num -= leisure_num

            if residual_need_num == 0:
                need_NIC_list = tmp_NIC_record
            else:
                # Cannot allocate a new task. Rollback!
                for NIC_id in tmp_NIC_record:
                    self._switch_leisure_NIC_num_map[self.belong_which_leaf_switch(NIC_id)] += 1
                allocate_succeed = False
                return allocate_succeed, need_NIC_list, allocated_link_mapping, all_gpu_index, link_mapping
            
            # --- old ---
            # unoccpuied_NIC_list = list(unoccpuied_NIC_set)
            # unoccpuied_NIC_list = sorted(unoccpuied_NIC_list)
            # need_NIC_list = [unoccpuied_NIC_list[i] for i in range(task_occupied_NIC_num)]
            # ------

            self._task_NIC_map[taskid] = need_NIC_list

            leaf_switch_list = []
            allocated_link_mapping = []
            switch_NIC_cnt = {}
            for NIC_id in need_NIC_list:
                switch_id = self.belong_which_leaf_switch(NIC_id)
                if switch_NIC_cnt.get(switch_id):
                    switch_NIC_cnt[switch_id] += 1
                else:
                    switch_NIC_cnt[switch_id] = 1

                leaf_switch_list.append(switch_id)
                # Links between NICs and leaf switches.
                allocated_link_mapping.append((NIC_id, switch_id, 1))
                allocated_link_mapping.append((switch_id, NIC_id, 1))

                self._record_occupied_NIC_set.add(NIC_id)


            leaf_switch_set = set(leaf_switch_list)
            leaf_switch_list = sorted(list(leaf_switch_set))
            switch_num = len(leaf_switch_list)

            if switch_num == 2:
                allocated_link_mapping.append((leaf_switch_list[0], leaf_switch_list[1], int(task_occupied_NIC_num / 2)))
                allocated_link_mapping.append((leaf_switch_list[1], leaf_switch_list[0], int(task_occupied_NIC_num / 2)))
            elif switch_num > 2:
                min_switch_NIC_cnt = float("inf")
                max_switch_NIC_cnt = -1
                for k, v in switch_NIC_cnt.items():
                    if v < min_switch_NIC_cnt:
                        min_switch_NIC_cnt = v
                    if v > max_switch_NIC_cnt:
                        max_switch_NIC_cnt = v

                available_port_num = max_switch_NIC_cnt * (self._leaf_switch_port_num - self._downlinks) / self._downlinks
                
                if switch_num <= available_port_num:
                    link_num = math.floor(available_port_num / (switch_num - 1))
                    # Links between leaf switches.
                    for i in range(switch_num):
                        for j in range(switch_num):
                            if i != j:
                                allocated_link_mapping.append((leaf_switch_list[i], leaf_switch_list[j], link_num))
                else:
                    print('Debug: switch_num > available_port_num!!!', switch_num, available_port_num)
                    print(need_NIC_list)
                    print(task_occupied_NIC_num)
                    print(leaf_switch_list)
                    exit()

            allocate_succeed = True
            Simulator.TASK_SWITCH_DICT[taskid] = leaf_switch_list
            Simulator.TASK_NIC_DICT[taskid] = need_NIC_list

        return allocate_succeed, need_NIC_list, allocated_link_mapping, all_gpu_index, link_mapping


    def update_finished_job(self, taskid, current_time, waiting_task_list):
        NIC_list = self._task_NIC_map[taskid]
        for NIC_id in NIC_list:
            self._record_occupied_NIC_set.remove(NIC_id)
            self._switch_leisure_NIC_num_map[self.belong_which_leaf_switch(NIC_id)] += 1


    def belong_which_leaf_switch(self, NIC_id):
        return NIC_id // self._downlinks + self._NIC_num


    def _get_leisure_NIC_set(self):
        all_NIC_set = set([i for i in range(self._NIC_num)])
        return all_NIC_set ^ self._record_occupied_NIC_set


    def _get_NIC_list_in_switch(self, switch_id, downlinks, NIC_num, need_num):
        if need_num == downlinks:
            return [i for i in range((switch_id - NIC_num) * downlinks, (switch_id - NIC_num + 1) * downlinks)]
        elif need_num < downlinks:
            leisure_NIC_set = self._get_leisure_NIC_set()
            switch_NIC_set = set([i for i in range((switch_id - NIC_num) * downlinks, (switch_id - NIC_num + 1) * downlinks)])
            
            can_be_used = switch_NIC_set & leisure_NIC_set
            res = []
            for NIC_id in can_be_used:
                res.append(NIC_id)
                need_num -= 1
                if need_num <= 0:
                    break
            return res
        elif need_num > downlinks:
            print("Bug: _get_NIC_list_in_switch need_num > downlinks")
            return