

from rapidnetsim.core.event.event import Event
from rapidnetsim.core.infrastructure.task_step import TaskStep

class FlowTransmitEvent(Event):
    """Trigger all the flows in flow_list at the same time.
    """
    def __init__(self, time_from_now, flow_list) -> None:
        super().__init__(time_from_now)
        self._flow_list = flow_list
        self._type_priority = 1


    def do_sth(self):
        """Start all the flows in flow_list.
        """
        from rapidnetsim.core.simulator import Simulator

        across_network = False
        for flow in self._flow_list:
            src = flow.get_src()
            dst = flow.get_dst()
            taskid = flow.get_taskid()
            stepid = flow.get_stepid()
            flowid = flow.get_flowid()

            flow_size = flow.get_size()
                
            flow.find_hop_list()
            hop_list = flow.get_hop_list()


            if not flow.is_in_the_same_server():
                across_network = True

            flow.set_start_time(Simulator.get_current_time())
            flow.set_last_calculated_time(Simulator.get_current_time())

            # infra = Simulator.get_infrastructure()
            # If NIC_src and NIC_dst belong to the same server, 
            # do not accupy links bandwidth.

            # Start subsequent paths.
            next_hop = None
            tmp_src = src
            if hop_list == []:
                Simulator.add_task_step_link_occupy(taskid, stepid, src, dst, 0)

            for next_hop, relative_port in hop_list:
                # Ongoing path is (tmp_src, next_hop)
                # Necessary: Refresh network occupied condition.
                # infra.add_link_flow_occupy(flowid, tmp_src, next_hop, taskid)
                Simulator.add_task_step_link_occupy(taskid, stepid, tmp_src, next_hop, relative_port)

                # Update next hop path
                tmp_src = next_hop
            
            # infra.set_flow_infly_info(flowid, flow, taskid)    # Necessary

        Simulator.set_inflight_taskstep_info(taskid, TaskStep(taskid, stepid, flow_size, across_network))
