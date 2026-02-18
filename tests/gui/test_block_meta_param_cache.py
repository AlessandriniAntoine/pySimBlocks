from pySimBlocks.gui.blocks.block_dialog_session import BlockDialogSession
from pySimBlocks.gui.blocks.controllers.pid import PIDMeta
from pySimBlocks.gui.models.block_instance import BlockInstance


def test_gather_params_keeps_inactive_values_for_cache():
    meta = PIDMeta()
    instance = BlockInstance(meta)
    session = BlockDialogSession(meta, instance)

    session.local_params["controller"] = "PD"  # Ki inactive for PD
    session.local_params["Ki"] = 10

    gathered = meta.gather_params(session)

    assert gathered["Ki"] == 10
