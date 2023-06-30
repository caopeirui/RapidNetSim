import pandas as pd


def get_cwnd_log_data(filename):
    df_data = pd.read_csv(filename, header = None)
    df_data.columns = ['flowid', 'cwnd', 'ctime']
    return df_data


def get_cwnd_list_by_flowid(df_data, flowid):
    return df_data[df_data['flowid'] == flowid].reset_index()


def get_statistics_by_interval(df_data, left_interval, right_interval):
    return df_data.query(f'ctime > {left_interval} and ctime <= {right_interval}')


def get_cwnd_ratio_dict_from_logfile(filename):
    df_data = get_cwnd_log_data(filename)
    flowid_set = set(df_data['flowid'])

    cwnd_ratio_dict = {}

    flow_end_time_dict = {}
    for flowid in flowid_set:
        flow_end_time_dict[flowid] = get_cwnd_list_by_flowid(df_data, flowid)['ctime'].max()
    
    flow_end_time_list = sorted(flow_end_time_dict.items(), key = lambda d: d[1])
    max_index = len(flow_end_time_dict)
    for index, (flowid, end_time) in enumerate(flow_end_time_list):
        if index == max_index - 1:
            break
        if index == 0:
            left_interval = 0
            right_interval = end_time
        else:
            left_interval = flow_end_time_list[index - 1][1]
            right_interval = end_time
        
        idata = get_statistics_by_interval(df_data, left_interval, right_interval)
        interval_mean = idata.groupby('flowid').mean().reset_index()
        interval_median = idata.groupby('flowid').median().reset_index()
        
        interval_res = interval_median
        key = tuple(interval_res['flowid']) 
        tmp_sum = interval_res['cwnd'].sum()
        cur_cwnd_ratio = {}
        for i in key:
            cur_cwnd_ratio[i] = interval_res.query(f'flowid == {i}')['cwnd'].values[0] / tmp_sum

        cwnd_ratio_dict[key] = cur_cwnd_ratio

    return cwnd_ratio_dict


if __name__ == "__main__":
    get_cwnd_ratio_dict_from_logfile('/Users/cpr/Desktop/sync-ubuntu/ingenious_datacenters/trigger_compare_rapidnetsim_ecmp/experiment/index7200_coe1/result/congestion_window.csv.log')

