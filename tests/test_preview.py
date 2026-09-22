from preview import preview_decision


def test_offline_preview_decisions():
    assert preview_decision("from DXB\nto Dubai Marina\nPrice: €16", ["Accept"]).startswith("WOULD CLICK ACCEPT")
    assert preview_decision("from DXB\nto Dubai Marina\nPrice: €15", ["Accept"]).startswith("IGNORE: price")
    assert preview_decision("from DXB\nto Sharjah\nPrice: €30", ["Accept"]).startswith("IGNORE: drop-off")
    assert preview_decision("from DXB\nto Dubai Marina\nPrice: €30", ["Make an offer"]).startswith("IGNORE: booking type")
