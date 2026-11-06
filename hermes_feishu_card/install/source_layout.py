"""Fixed source-family identities; layout alone does not prove hook support."""

DECOMPOSED_GATEWAY_TARGETS = (
    "gateway/run_turn.py", "gateway/run_turn_persistence.py", "gateway/run_turn_prepare.py", "gateway/run_turn_hygiene.py",
    # v0.22.6 moved the background-task mixin into its own module; it carries no
    # HFC hook of its own, but the inherited completion ownership is proven
    # through it, so it joins the managed (byte-restored) source set.
    "gateway/run_background.py",
    # v0.22 moved the progress callbacks (status, tool, interim) onto a mixin in
    # this module; it is a managed target so their hooks can be installed there.
    "gateway/run_turn_progress.py", "gateway/run_turn_runner.py", "gateway/run_inbound.py",
    "gateway/run_busy.py", "gateway/run_startup.py", "gateway/run_notifications.py",
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
