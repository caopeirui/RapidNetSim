import os
import sys
import configparser
import time

from rapidnetsim.core.simulator import Simulator
from rapidnetsim.task.task_generator import Task



if __name__ == "__main__":
    # Cmd control and instructions
    if len(sys.argv) < 2:
        print('Please add config filename, eg: python3 main.py exp.ini')
    else:
        conf_filename = sys.argv[1]

    conf_handler = configparser.ConfigParser()
    conf_handler.optionxform = lambda option: option    # Enable case sensitive

    conf_handler.read(conf_filename)

    print(f'Load confile: {os.getcwd()}/{conf_filename}')

    Simulator.init_logger()

    Simulator.setup(conf_handler)

    start_time = time.time()

    # Create network infrastructure
    Simulator.create_infrastructure()

    # Scheduler
    joint_scheduler = Simulator.CONF_DICT['joint_scheduler']
    print('joint_scheduler =', joint_scheduler, flush = True)
    Simulator.load_scheduler()

    # Generate tasks
    task_obj = Task()
    task_obj.generate()

    Simulator.core_run()

    Simulator.clos_logger()

    end_time = time.time()


    print('Conflicting flows num:', Simulator.CONFLICT_TASKSTEPFLOW_RECORD)
    print('Max flowid:', Simulator.FLOWID - 1)
    if Simulator.FLOWID > 1:
        print('Conflicting flow proportion:', Simulator.CONFLICT_TASKSTEPFLOW_RECORD / (Simulator.FLOWID - 1))

    print('Simulation execution time:', end_time - start_time)

    # The test of task completion time
    if len(sys.argv) >= 3 and sys.argv[2] == 'test':
        from rapidnetsim.utils.test_task_time import test_a_task_completion_time
        task_seq = 0
        expected_completion_time = Simulator._task_type_obj.get_expected_completion_time(task_seq)
        task_log_file = f'{os.getcwd()}/task_time.log'
        test_a_task_completion_time(expected_completion_time, task_log_file, task_seq)
