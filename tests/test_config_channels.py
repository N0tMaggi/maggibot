import handlers.config as cfg


class DummyGuild:
    def __init__(self, guild_id: int, channels: dict[int, object]):
        self.id = guild_id
        self._channels = channels

    def get_channel(self, channel_id: int | None):
        if not channel_id:
            return None
        return self._channels.get(channel_id)


def test_get_protection_log_channel_prefers_protectionlogchannel(monkeypatch):
    guild = DummyGuild(123, {10: object(), 20: object()})

    def fake_load():
        return {"123": {"protectionlogchannel": 10, "logchannel": 20}}

    monkeypatch.setattr(cfg, "loadserverconfig", fake_load)

    assert cfg.get_protection_log_channel(guild) is guild.get_channel(10)


def test_get_protection_log_channel_falls_back_to_logchannel(monkeypatch):
    guild = DummyGuild(123, {20: object()})

    def fake_load():
        return {"123": {"logchannel": 20}}

    monkeypatch.setattr(cfg, "loadserverconfig", fake_load)

    assert cfg.get_protection_log_channel(guild) is guild.get_channel(20)
