global STORE
STORE = {
    'traces': [],
    'metrics': [],
    'logs': []
}

async def add_trace_to_store(item: dict) -> None:
    global STORE
    STORE['traces'].append(item)

async def add_metrics_to_store(item: dict) -> None:
    global STORE
    STORE['metrics'].append(item)

async def add_logs_to_store(item: dict) -> None:
    global STORE
    STORE['logs'].append(item)
