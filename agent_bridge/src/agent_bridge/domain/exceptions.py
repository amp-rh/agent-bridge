class AgentExecutionError(RuntimeError):
    pass


class AgentTimeoutError(AgentExecutionError):
    pass


class ConfigError(ValueError):
    pass
