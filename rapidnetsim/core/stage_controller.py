


def del_global_record_trigger_new_step(taskid, stepid):
    """After every step in a task is finished, check the task if is finished.
    And trigger new step.
    """
    from rapidnetsim.core.simulator import Simulator
    from rapidnetsim.core.event.flow_transmit_event import FlowTransmitEvent

    Simulator.del_a_wait_transmit_flow(taskid, stepid)
    flow_list = []

    if Simulator.get_wait_transmit_dict().get(f'{taskid}_{stepid + 1}'):
        for flowid, flow in Simulator.get_wait_transmit_dict()[f'{taskid}_{stepid + 1}'].items():
            # Note that Time recorded in Flow structure is absolute time,
            # while time in Event triggered by Simulator is relative time. 
            flow.set_last_calculated_time(Simulator.get_current_time())
            flow_list.append(flow)

        computation_time = float(Simulator.CONF_DICT['computation_time'])
        Simulator.register_event(FlowTransmitEvent(computation_time, flow_list))
    else:
        print(f'Task {taskid} is done at time {Simulator.get_current_time()}!')

        Simulator.task_time_logger.write(f'taskid,{taskid},finish_time,{Simulator.get_current_time()}\n')

        scheduler = Simulator.get_scheduler()

        scheduler.update_finished_job(taskid, Simulator.get_current_time(), Simulator.WAITING_TASK_LIST)

        _detect_and_trigger_a_task()


def _detect_and_trigger_a_task():
    from rapidnetsim.core.simulator import Simulator

    # Modify according to scheduling algorithm.
    if len(Simulator.WAITING_TASK_LIST) > 0:
        scheduler = Simulator.get_scheduler()
        while True:
            a_waiting_task = Simulator.pop_a_waiting_task()
            (arriving_time, model_size, task_occupied_NIC_num, task_type_obj, taskid, task_type, task_iteration_num, NIC_num_in_a_server) = a_waiting_task.get_task_info_tuple()
            allocate_succeed, use_NIC_list = allocate_a_task(scheduler, model_size, task_occupied_NIC_num, task_type_obj, taskid)
            if allocate_succeed == True:
                continue_record_more_iteration_if_need(taskid, task_occupied_NIC_num, model_size, task_type, task_type_obj, task_iteration_num, NIC_num_in_a_server, use_NIC_list)

                if len(Simulator.WAITING_TASK_LIST) == 0:
                    return
            else:
                Simulator.push_a_waiting_task(a_waiting_task)
                break
        return


def allocate_a_task(scheduler, model_size, task_occupied_NIC_num, task_type_obj, taskid):
    from rapidnetsim.core.simulator import Simulator
    NIC_num_in_a_server = int(Simulator.CONF_DICT['NIC_num_in_a_server'])

    current_time = Simulator.get_current_time()
    Simulator.waiting_task_logger.write(f'{current_time},{len(Simulator.WAITING_TASK_LIST)}\n')

    not_need_refresh = True

    allocate_succeed, gpu_indexes, allocated_link_mapping, all_gpu_index, link_mapping = scheduler.schedule(task_occupied_NIC_num, taskid, current_time, Simulator.WAITING_TASK_LIST)

    if allocate_succeed == True:
        temp_used_leaf_list = []
        for temp_gpu in gpu_indexes:
            temp_leaf_index = int(temp_gpu/32)
            if temp_leaf_index not in temp_used_leaf_list:
                temp_used_leaf_list.append(temp_leaf_index)
        
        if Simulator.CONF_DICT['joint_scheduler'] in ['mesh_scheduler', 'mesh_cross', 'GPUPlacemeter', 'GPUPlacemeter2', 'GPUPlacemeter3', 'StaticPlacementer', 'hw_oxc_all2all', 'hw_oxc_all2all_sz', 'hw_oxc_all2all2', 'hw_oxc_allreduce', 'hw_oxc_hdallreduce', 'hw_oxc_allreduce_nopeer']:
            # Update topology and path dict
            Simulator.reconfigure(allocated_link_mapping, taskid)
            print("finish reconfig")

        Simulator.TASK_FULL_OCS_PREPARE_DICT[taskid] = _prepare_maping(gpu_indexes)
        task_type_obj.deal_job(
            taskid = taskid,
            model_size = model_size,
            task_occupied_NIC_num = task_occupied_NIC_num,
            use_NIC_list = gpu_indexes,
            NIC_num_in_a_server = NIC_num_in_a_server,
        )

        return True, gpu_indexes
    else:
        return False, None


def continue_record_more_iteration_if_need(taskid, task_occupied_NIC_num, model_size, task_type, task_type_obj, iteration_num, NIC_num_in_a_server, use_NIC_list):
    from rapidnetsim.core.simulator import Simulator

    a_iteration_finish_cnt = len(task_type_obj.get_task_a_iteration_pair_list(task_occupied_NIC_num, model_size, NIC_num_in_a_server, use_NIC_list))
    Simulator.ITERATION_FINISH_ROUNDID_DICT[taskid] = [a_iteration_finish_cnt * i - 1 for i in range(1, iteration_num + 1)]

    from rapidnetsim.core.infrastructure.flow import Flow
    round_pair_list = task_type_obj.get_task_a_iteration_pair_list(task_occupied_NIC_num, model_size, NIC_num_in_a_server, use_NIC_list)
    roundid = len(round_pair_list)
    for _ in range(1, iteration_num):
        for pair_list in round_pair_list:
            # Every round
            for (src, dst, communication_size) in pair_list:
                # use_NIC_list[src] maps old may-occupied NIC_id to new unoccupied NIC_id
                flow = Flow(
                    Simulator.FLOWID, communication_size, None, use_NIC_list[src], use_NIC_list[dst],
                    communication_size, None,
                    taskid, roundid, task_occupied_NIC_num, False, use_NIC_list
                )
                task_type_obj.record_network_occupy(taskid, roundid, flow, use_NIC_list[src])
                Simulator.FLOWID += 1
            roundid += 1


def _prepare_maping(use_NIC_list):
    from rapidnetsim.core.simulator import Simulator
    NIC_num_in_a_server = int(Simulator.CONF_DICT['NIC_num_in_a_server'])

    server_ids = []
    server_nic_map = {}
    absolute_nic_to_relative_indices = {}

    for nic in use_NIC_list:
        server_id = nic // NIC_num_in_a_server
        if server_id not in server_ids:
            server_ids.append(server_id)
        if server_nic_map.get(server_id):
            server_nic_map[server_id].append(nic)
        else:
            server_nic_map[server_id] = [nic]
    
    for relative_server_id in range(len(server_ids)):
        absolute_server_id = server_ids[relative_server_id]
        for relative_intra_nic_id in range(len(server_nic_map[absolute_server_id])):
            absolute_nic = server_nic_map[absolute_server_id][relative_intra_nic_id]
            absolute_nic_to_relative_indices[absolute_nic] = (relative_server_id, relative_intra_nic_id)

    return server_ids, server_nic_map, absolute_nic_to_relative_indices
