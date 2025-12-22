class ConnectionInstance:
    def __init__(
        self,
        src_block,
        src_port,
        dst_block,
        dst_port,
    ):
        self.src_block = src_block        # BlockInstance
        self.src_port = src_port          # str
        self.dst_block = dst_block        # BlockInstance
        self.dst_port = dst_port          # str
