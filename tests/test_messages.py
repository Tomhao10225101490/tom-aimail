from tom_aimail import messages


def test_pick_language():
    assert messages.pick_language("homework help", "please") == "en"
    assert messages.pick_language("帮我看看", "") == "zh"
    assert messages.pick_language("", "请回答问题") == "zh"


def test_is_help_request():
    assert messages.is_help_request("help", "")
    assert messages.is_help_request("帮助", "")
    assert messages.is_help_request("Re: homework", "使用说明\nplease")
    assert not messages.is_help_request("help with homework", "please answer")


def test_templates_carry_the_key_information():
    assert "tom@qq.com" in messages.help_text("en", "tom@qq.com")
    assert "tom@qq.com" in messages.help_text("zh", "tom@qq.com")
    assert "Got it" in messages.ack_text("en", "x")
    assert "收到啦" in messages.ack_text("zh", "x")
