from pySimBlocks.gui.blocks.sources.file_source import FileSourceMeta


def test_file_source_meta_conditional_parameters():
    meta = FileSourceMeta()

    npz_values = {"file_path": "data.npz"}
    assert meta.is_parameter_active("key", npz_values) is True

    npy_values = {"file_path": "data.npy"}
    assert meta.is_parameter_active("key", npy_values) is False

    csv_values = {"file_path": "data.csv"}
    assert meta.is_parameter_active("key", csv_values) is True
