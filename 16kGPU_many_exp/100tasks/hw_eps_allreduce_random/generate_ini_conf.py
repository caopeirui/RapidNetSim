from jinja2 import Environment, PackageLoader
from base_conf_template.create_clos import create_hw_eps_connect_list, create_hw_eps_3layer_connect_list
from base_conf_template.generate_tasks import generate_custom_tasks, generate_16384_custom_tasks2

if __name__ == '__main__':
    NIC_num = 16384
    leaf_switch_num = 1024
    leaf_switch_port_num = 64
    downlinks = 32
    spine_switch_num = 256
    spine_switch_port_num = 64
    NIC_num_in_a_server = 128


    joint_scheduler = 'hw_eps_allreduce'

    # [(arriving_time, model_size at every NIC, task_occupied_NIC_num), ...]
    task_list = generate_16384_custom_tasks2(200, exponential_beta = 0.0004, fixed_model_size = 8)

    connect_info_list = create_hw_eps_connect_list(NIC_num, leaf_switch_num, spine_switch_num, leaf_switch_port_num, spine_switch_port_num, NIC_num_in_a_server)
    connect_info_str = str(connect_info_list)

    env = Environment(loader = PackageLoader('base_conf_template', './'))
    template = env.get_template('base_ini_template.j2')
    content = template.render(
        connect_info_str = connect_info_str,
        topo_type = 'clos',
        find_path_method = 'shortest',
        joint_scheduler = joint_scheduler,
        measure_sampling_interval = 10,

        downlinks = downlinks,

        find_next_hop_method = 'random',
        
        waiting_task_order_mode = 'FIFO',
        # waiting_task_order_mode = 'few_GPU_first',
        # waiting_task_order_mode = 'small_task_first',

        NIC_num = NIC_num,
        NIC_num_in_a_server = NIC_num_in_a_server,

        leaf_switch_num = leaf_switch_num,

        leaf_switch_port_num = leaf_switch_port_num,
        spine_switch_port_num = spine_switch_port_num,

        spine_switch_num = spine_switch_num,

        inner_server_bandwidth = 120,
        switch_port_bandwidth = 80,

        computation_time = 0,

        # task_type = 'compare_with_netbench',
        task_type = joint_scheduler,
        task_list = task_list,
        task_iteration_num = 1,

        # core_run_type = 'time_tick_based',
        # time_tick = 100,  # Unit: ns
        reconfiguration = 'no',

        network_transmission_delay = 0.00007,
        inserver_transmission_delay = 0.00001,

        non_overlap_ratio = 1,
    )
    with open('exp.ini', 'w') as f:
        f.write(content)
