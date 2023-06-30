

from rapidnetsim.core.event.event import Event
from rapidnetsim.core.infrastructure.task_step import TaskStep

class TaskStepFinishEvent(Event):
    """
    """
    def __init__(self, time_from_now, taskstep : TaskStep) -> None:
        super().__init__(time_from_now)
        self._taskstep = taskstep
        self._type_priority = 0


    def __str__(self) -> str:
        print_dict = {
            'event_time': self.get_event_time(), 
            'taskstep': self._taskstep,
        }
        print_str = '<TaskStepFinishEvent | '
        for key, val in print_dict.items():
            print_str += key + ': ' + str(val) + ', '
        print_str += '>'
        return print_str


    def do_sth(self):
        from rapidnetsim.core.simulator import Simulator
        from rapidnetsim.core.stage_controller import del_global_record_trigger_new_step
        taskid = self._taskstep.get_taskid()
        stepid = self._taskstep.get_stepid()

        task_step_link_occupy = Simulator.get_task_step_link_occupy(taskid, stepid)
        for (src, dst, relative_port) in task_step_link_occupy:
            Simulator.del_link_occupied_for_tasks(taskid, src, dst, relative_port)

        Simulator.del_task_step_link_occupy(taskid, stepid)
        Simulator.del_inflight_taskstep_info(taskid)

        if len(Simulator._event_q) == 0:
            del_global_record_trigger_new_step(taskid, stepid)
        elif Simulator._event_q[0].get_event_time() > Simulator._current_time:
            del_global_record_trigger_new_step(taskid, stepid)
