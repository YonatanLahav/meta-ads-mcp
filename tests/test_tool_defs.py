from src.tools.campaign import get_campaign_tool_defs

EXPECTED_TOOLS = ["list_campaigns", "get_campaign", "create_campaign", "update_campaign", "delete_campaign"]


class TestCampaignToolDefs:
    def test_returns_five_tools(self):
        tools = get_campaign_tool_defs()
        assert len(tools) == 5

    def test_tool_names(self):
        tools = get_campaign_tool_defs()
        names = [t.name for t in tools]
        assert names == EXPECTED_TOOLS

    def test_all_have_schemas(self):
        tools = get_campaign_tool_defs()
        for tool in tools:
            assert tool.description
            schema = tool.inputSchema
            assert schema["type"] == "object"
            assert "properties" in schema

    def test_required_fields(self):
        tools = get_campaign_tool_defs()
        by_name = {t.name: t for t in tools}

        assert by_name["list_campaigns"].inputSchema["required"] == ["account_id"]
        assert by_name["get_campaign"].inputSchema["required"] == ["campaign_id"]
        assert by_name["create_campaign"].inputSchema["required"] == ["account_id", "name", "objective"]
        assert by_name["update_campaign"].inputSchema["required"] == ["campaign_id"]
        assert by_name["delete_campaign"].inputSchema["required"] == ["campaign_id"]
