from inference.gcn import predict_trace_class


if __name__ == "__main__":
    trace_lines = open('traces.csv', 'r').read().split('\n')
    headers = trace_lines[0].split(',')
    traces = [
        {headers[j]: trace_lines[i].split(',')[j] for j in range(0, len(headers))}
        for i in range(1, len(trace_lines)-1)
    ]

    predict_trace_class(traces, './gcn_conf.json')
