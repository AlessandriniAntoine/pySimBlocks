from pySimBlocks.gui.blocks.sources.function_source import FunctionSourceMeta
from pySimBlocks.gui.models.block_instance import BlockInstance


def test_function_source_meta_definition():
    meta = FunctionSourceMeta()

    assert meta.category == "sources"
    assert meta.type == "function_source"
    assert [p.name for p in meta.parameters] == [
        "file_path",
        "function_name",
        "output_keys",
        "sample_time",
    ]
    assert len(meta.inputs) == 0
    assert len(meta.outputs) == 1
    assert meta.outputs[0].name == "out"


def test_function_source_meta_resolves_dynamic_output_ports():
    meta = FunctionSourceMeta()
    instance = BlockInstance(meta)
    instance.update_params({"output_keys": ["y", "z"]})
    instance.resolve_ports()

    outputs = [p for p in instance.ports if p.direction == "output"]
    assert [p.name for p in outputs] == ["y", "z"]
