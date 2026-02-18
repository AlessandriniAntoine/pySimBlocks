from pySimBlocks.gui.blocks.sources.function_source import FunctionSourceMeta


def test_function_source_meta_definition():
    meta = FunctionSourceMeta()

    assert meta.category == "sources"
    assert meta.type == "function_source"
    assert [p.name for p in meta.parameters] == [
        "file_path",
        "function_name",
        "sample_time",
    ]
    assert len(meta.inputs) == 0
    assert len(meta.outputs) == 1
    assert meta.outputs[0].name == "out"
