"""rampart_20x_playground plugin AppConfig. Data, plus one panel type (req-rampart-20x-playground-nongoals)."""

from tap_plugins.base import TapPluginConfig


class Rampart20xPlaygroundConfig(TapPluginConfig):
    def ready(self) -> None:
        super().ready()  # MUST run first: it loads tap-plugin.toml

        # The countdown panel type (req-rampart-20x-playground-page-reporting-10). Imported and registered in ready(),
        # after every app has loaded.
        from tap_plugin.rampart_20x_playground.panels.countdown import RampartCountdownPanelType

        from tap_web.registry import panel_type_registry

        panel_type_registry.register(RampartCountdownPanelType.slug, RampartCountdownPanelType)
