from .fixture import AppTestCase


class TestPlayer(AppTestCase):

    steam_ids = [
        "76561198043212328",  # shire
        "76561198257384619",  # HanzoHasashiSan
        "76561197985202252",  # carecry
        "76561198308265738",  # lookaround
        "76561198257327401",  # Jalepeno
        "76561198005116094",  # Xaero
        "76561198077231066",  # Mike_Litoris
        "76561198346199541",  # Zigurun
        "76561198257338624",  # indie
        "76561198260599288",  # eugene
    ]

    def test_player_json(self):
        for steam_id in self.steam_ids:
            resp = self.get("/player/{0}.json".format(steam_id))

            obj_defacto = resp.json()
            obj_expected = self.read_json_sample("player_{}".format(steam_id))
            assert obj_defacto == obj_expected

            resp = self.get("/player/{0}".format(steam_id))
            assert resp.template.name == "player_stats.html"
            context = resp.context
            assert "request" in context
            assert "steam_id" in context
            assert context["steam_id"] == steam_id

            del context["request"]
            del context["steam_id"]
            obj_defacto = context
            assert obj_defacto == obj_expected

    def test_deprecated_player_json(self):
        for steam_id in self.steam_ids:
            resp = self.get("/deprecated/player/{0}.json".format(steam_id))
            assert resp.json() == \
                self.read_json_sample("deprecated_player_{0}".format(steam_id))
