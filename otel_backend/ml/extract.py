from otel_backend.ml import logger

async def extract_data(trace):
    data = trace.get('resourceSpans', [])
    extracted_info = []
    for item in data:
        item_info = {
            'ip_source': '',
            'ip_destination': '',
            'labels': {
                'pod_label': '',
                'namespace_label': '',
                'source_port_label': '',
                'destination_port_label': ''
            }
        }
        try:
            for attribute in item['resource']['attributes']:
                if attribute['key'] == 'k8s.namespace.name':
                    item_info['labels']['namespace_label'] = attribute['value']['stringValue']
                elif attribute['key'] == 'k8s.pod.name':
                    item_info['labels']['pod_label'] = attribute['value']['stringValue']

            for scopeSpan in item['scopeSpans']:
                for span in scopeSpan['spans']:
                    for attribute in span['attributes']:
                        if attribute['key'] == 'cilium.flow_event.IP.source':
                            item_info['ip_source'] = attribute['value']['stringValue']
                        elif attribute['key'] == 'cilium.flow_event.IP.destination':
                            item_info['ip_destination'] = attribute['value']['stringValue']
                        elif attribute['key'] == 'cilium.flow_event.l4.TCP.source_port':
                            item_info['labels']['source_port_label'] = attribute['value']['stringValue']
                        elif attribute['key'] == 'cilium.flow_event.l4.TCP.destination_port':
                            item_info['labels']['destination_port_label'] = attribute['value']['stringValue']
                        elif attribute['key'] == 'cilium.flow_event.l4.TCP.flags.ACK':
                            item_info['labels']['ack_flag'] = attribute['value']['stringValue']
                        elif attribute['key'] == 'cilium.flow_event.l4.TCP.flags.PSH':
                            item_info['labels']['psh_flag'] = attribute['value']['stringValue'] == 'true'
            extracted_info.append(item_info)
        except KeyError as e:
            logger.error(f"Key error: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
    return extracted_info
