from fastapi import Request


def get_checkpointer(request: Request):
    return request.app.state.checkpointer
