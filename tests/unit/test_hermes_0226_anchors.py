"""Hermes v0.22.6 anchor adaptation: new mixin module, ctx-shaped status callback.

v0.22 moved the progress callbacks out of ``_run_agent``'s closures onto
``GatewayTurnProgressMixin`` (gateway/run_turn_progress.py) and reads the turn
state through ``ctx``. The status hook must install there without weakening the
old-shape contract, so both callbacks are exercised against the rendered block.
"""
import ast

import pytest

from hermes_feishu_card import admission_completion
from hermes_feishu_card.install import patcher
from hermes_feishu_card.install.source_layout import DECOMPOSED_GATEWAY_TARGETS


V0226_STATUS_MODULE = '''
class GatewayTurnProgressMixin:
    def _status_callback_sync(self, event_type: str, message: str) -> None:
        from gateway.run import _prepare_gateway_status_message
        ctx = self._ctx
        if ctx.mute_notification_reply or not self._status_live():
            return
        prepared = _prepare_gateway_status_message(ctx.source.platform, event_type, message)
        if prepared is None:
            return
        present = lambda: None
        present()
'''


def _body_location(module_text: str, name: str, **kwargs):
    tree = ast.parse(module_text)
    return patcher._find_mixin_callback_body_location(
        tree, module_text.splitlines(keepends=True), name, **kwargs
    )


def test_ctx_shaped_status_callback_is_located():
    assert _body_location(V0226_STATUS_MODULE, "_status_callback_sync",
                          required_ctx_attrs=("source",)) is not None


def test_callback_without_turn_context_binding_is_not_located():
    unbound = V0226_STATUS_MODULE.replace("ctx = self._ctx", "ctx = None")
    assert _body_location(unbound, "_status_callback_sync",
                          required_ctx_attrs=("source",)) is None


def test_callback_missing_a_required_ctx_attribute_is_not_located():
    stripped = V0226_STATUS_MODULE.replace("ctx.source.platform", "unknown.platform")
    assert _body_location(stripped, "_status_callback_sync",
                          required_ctx_attrs=("source",)) is None


@pytest.mark.parametrize("shape", ["ctx", "closure"])
def test_rendered_status_hook_compiles_for_both_callback_shapes(shape):
    block = "".join(patcher._render_status_hook_block("        ", "\n"))
    if shape == "ctx":
        method = (
            "class M:\n"
            "    def _status_callback_sync(self, event_type: str, message: str) -> None:\n"
            "        ctx = self._ctx\n"
            + block +
            "        return None\n"
        )
    else:
        method = (
            "class M:\n"
            "    def _run_agent(self):\n"
            "        def _status_callback_sync(event_type: str, message: str) -> None:\n"
            "            source = None\n"
            "            _status_chat_id = None\n"
            "            event_message_id = None\n"
            "            _loop_for_step = None\n"
            "            def _run_still_current():\n"
            "                return True\n"
            + "".join("        " + line + "\n" for line in block.splitlines()) +
            "            return None\n"
            "        return _status_callback_sync\n"
        )
    compile(method, "<status-hook>", "exec")
    # Both deictic lookups must be present: the closure names and the ctx fallbacks.
    assert 'locals().get("ctx") or getattr(self, "_ctx", None)' in block
    assert 'getattr(_hfc_ctx, "source", None)' in block


def test_v022_modules_join_the_managed_source_set():
    assert "gateway/run_turn_progress.py" in DECOMPOSED_GATEWAY_TARGETS
    assert "gateway/run_background.py" in DECOMPOSED_GATEWAY_TARGETS


def test_completion_ownership_accepts_the_v0226_background_base():
    source = ast.get_source_segment(
        open(patcher.__file__, encoding="utf-8").read(),
        next(
            node for node in ast.parse(open(patcher.__file__, encoding="utf-8").read()).body
            if isinstance(node, ast.FunctionDef) and node.name == "_split_completion_node"
        ),
    )
    assert "GatewayBackgroundMixin" in source
    assert "gateway.run_background" in source


def test_v0226_admission_source_pair_is_a_verified_cohort():
    pair = (
        "12466f9c31f57877c6ae8ea6189d76123a278bdc99e5242c13c5c4ecff0f8ae9",
        "207708e4aeb0bf2d8e577f145110a414d80c12da1c4e69570f0402f7d7f6d1a6",
    )
    pairs = {
        (cohort["gateway.session_ingress"], cohort["gateway.session_authority"])
        for cohort in admission_completion.SOURCE_COHORTS
    }
    assert pair in pairs
