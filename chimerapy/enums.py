# MANAGER, WORKER, and NODE can send
DATA_ACK = "DATA_ACK"
SHUTDOWN = "SHUTDOWN"

# SEND BY MANAGER
MANAGER_MESSAGE = "MANAGER_MESSAGE"
MANAGER_CREATE_NODE = "MANAGER_CREATE_NODE"
MANAGER_REQUEST_NODE_SERVER_DATA = "MANAGER_REQUEST_NODE_SERVER_DATA"
MANAGER_BROADCAST_NODE_SERVER_DATA = "MANAGER_BROADCAST_NODE_SERVER_DATA"
MANAGER_REPORT_STATUS = "MANAGER_REPORT_STATUS"
MANAGER_REQUEST_STEP = "MANAGER_REQUEST_STEP"
MANAGER_START_NODES = "MANAGER_START_NODES"
MANAGER_STOP_NODES = "MANAGER_STOP_NODES"
MANAGER_HEALTH_CHECK = "MANAGER_HEALTH_CHECK"
MANAGER_REQUEST_GATHER = "MANAGER_REQUEST_GATHER"

# SEND BY WORKER
WORKER_MESSAGE = "WORKER_MESSAGE"
WORKER_REGISTER = "WORKER_REGISTER"
WORKER_DEREGISTER = "WORKER_DEREGISTER"
WORKER_REPORT_HEALTH = "WORKER_REPORT_HEALTH"
WORKER_REPORT_NODE_SERVER_DATA = "WORKER_REPORT_NODE_SERVER_DATA"
WORKER_BROADCAST_NODE_SERVER_DATA = "WORKER_BROADCAST_NODE_SERVER_DATA"
WORKER_REPORT_NODES_STATUS = "WORKER_REPORT_NODES_STATUS"
WORKER_COMPLETE_BROADCAST = "WORKER_COMPLETE_BROADCAST"
WORKER_REQUEST_STEP = "WORKER_REQUEST_STEP"
WORKER_REQUEST_GATHER = "WORKER_REQUEST_GATHER"
WORKER_REPORT_GATHER = "WORKER_REPORT_GATHER"
WORKER_START_NODES = "WORKER_START_NODES"
WORKER_STOP_NODES = "WORKER_STOP_NODES"

# SEND BY NODE
NODE_MESSAGE = "NODE_MESSAGE"
NODE_STATUS = "NODE_STATUS"
NODE_DATA_TRANSFER = "NODE_DATA_TRANSFER"
NODE_CONN_MESSAGE = "NODE_CONN_MESSAGE"
NODE_REPORT_GATHER = "NODE_REPORT_GATHER"
