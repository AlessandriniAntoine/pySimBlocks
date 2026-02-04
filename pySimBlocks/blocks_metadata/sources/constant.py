from pySimBlocks.blocks_metadata.block_meta import BlockMetaAbstract

class ConstantBlock(BlockMetaAbstract):
    
    def __init__(self):
        self.name = "Constant"
        self.category = "sources"
        self.type = "constant"
        self.summary = "Constant signal source."
        self.description = """
  Generates a constant output signal:
  $$
  y(t) = c
  $$"""