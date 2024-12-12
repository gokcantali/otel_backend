# from inference.gcn import predict_trace_class
#
#
# if __name__ == "__main__":
#     traces = [
#         {"ip_source": "10.42.4.235", "ip_destination": "10.42.3.238", "is_anomaly": False, "source_pod_label": "back-end-green-58d676f6b4-fsbfm", "source_namespace_label": "green", "source_port_label": 51882, "destination_pod_label": "postgres-green-d95cfc494-kpzqt", "destination_namespace_label": "green", "destination_port_label": 80, "ack_flag": False, "psh_flag": False, "timestamp": "2024-12-11T15:57:48.481949084Z"},
#         {"ip_source": "10.42.3.238", "ip_destination": "10.42.4.235", "is_anomaly": False, "source_pod_label": "postgres-green-d95cfc494-kpzqt", "source_namespace_label": "green", "source_port_label": 80, "destination_pod_label": "back-end-green-58d676f6b4-fsbfm", "destination_namespace_label": "green", "destination_port_label": 51882, "ack_flag": True, "psh_flag": False, "timestamp": "2024-12-11T15:57:48.481959374Z"},
#         {"ip_source": "10.42.3.238", "ip_destination": "10.42.4.235", "is_anomaly": False, "source_pod_label": "postgres-green-d95cfc494-kpzqt", "source_namespace_label": "green", "source_port_label": 80, "destination_pod_label": "back-end-green-58d676f6b4-fsbfm", "destination_namespace_label": "green", "destination_port_label": 51882, "ack_flag": True, "psh_flag": True, "timestamp": "2024-12-11T15:57:48.482947252Z"},
#         {"ip_source": "10.42.4.235", "ip_destination": "10.42.3.238", "is_anomaly": False, "source_pod_label": "back-end-green-58d676f6b4-fsbfm", "source_namespace_label": "green", "source_port_label": 51882, "destination_pod_label": "postgres-green-d95cfc494-kpzqt", "destination_namespace_label": "green", "destination_port_label": 80, "ack_flag": True, "psh_flag": False, "timestamp": "2024-12-11T15:57:48.482960156Z"}
#     ]
#     predict_trace_class(traces, './gcn_conf.json')
