"""Fixed source-family identities; layout alone does not prove hook support."""

DECOMPOSED_GATEWAY_TARGETS = (
    "gateway/run_turn.py", "gateway/run_turn_persistence.py", "gateway/run_turn_prepare.py", "gateway/run_turn_hygiene.py", "gateway/run_turn_runner.py", "gateway/run_inbound.py",
    "gateway/run_busy.py", "gateway/run_startup.py", "gateway/run_notifications.py",
)
# v0.22 split these out of the facade: the background-task mixin moved to its own
# module (completion-ownership evidence, no hook of its own) and the progress
# callbacks moved onto a mixin in run_turn_progress.py. Older Hermes trees do not
# ship them, so they are optional sources: read and managed only when present.
DECOMPOSED_OPTIONAL_GATEWAY_TARGETS = (
    "gateway/run_background.py", "gateway/run_turn_progress.py",
)
DECOMPOSED_TARGETS = (*DECOMPOSED_GATEWAY_TARGETS,
                      "cron/scheduler_delivery.py", "gateway/platforms/base.py")


DECOMPOSED_MANIFEST_VERSION = 4
DECOMPOSED_LAYOUT = "gateway-decomposed-v1"
MANIFEST_NAME = ".hermes_feishu_card_manifest"
BACKUP_SUFFIX = ".hermes_feishu_card.bak"
DECOMPOSED_SOURCE_TARGETS = (
    "gateway/run.py", *DECOMPOSED_GATEWAY_TARGETS,
    "cron/scheduler.py", "cron/scheduler_delivery.py", "gateway/platforms/base.py",
)
DECOMPOSED_OPTIONAL_SOURCE_TARGETS = (
    "gateway/run_background.py", "gateway/run_turn_progress.py",
)
DECOMPOSED_ALL_SOURCE_TARGETS = (*DECOMPOSED_SOURCE_TARGETS,
                                 *DECOMPOSED_OPTIONAL_SOURCE_TARGETS)
