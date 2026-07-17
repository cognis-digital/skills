import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "x-twitter-scraper"
    / "run.py"
)
SPEC = importlib.util.spec_from_file_location("x_twitter_scraper", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_search_and_profile_urls_match_the_api_contract():
    search_target = MODULE.clean_target("@openai", "search")
    search = MODULE.build_plan("search", search_target, 3, MODULE.BASE_URL)
    user_target = MODULE.clean_target("@openai", "user")
    user = MODULE.build_plan("user", user_target, None, MODULE.BASE_URL)

    assert search["request"]["url"].endswith("/x/tweets/search?q=%40openai&limit=3")
    assert user["request"]["url"].endswith("/x/users/openai")


def test_followers_uses_the_current_page_size_parameter():
    target = MODULE.clean_target("@openai", "followers")
    plan = MODULE.build_plan("followers", target, 20, MODULE.BASE_URL)

    assert plan["request"]["url"].endswith("/x/users/openai/followers?pageSize=20")


@pytest.mark.parametrize(
    ("workflow", "target", "path", "body"),
    [
        (
            "media",
            "https://x.com/openai/status/123",
            "/api/v1/x/media/download",
            {"tweetInput": "https://x.com/openai/status/123"},
        ),
        (
            "monitor",
            "launch week",
            "/api/v1/monitors/keywords",
            {"query": "launch week", "eventTypes": ["tweet.new"]},
        ),
        (
            "webhook",
            "https://example.com/hook",
            "/api/v1/webhooks",
            {"url": "https://example.com/hook", "eventTypes": ["tweet.new"]},
        ),
    ],
)
def test_post_plans_match_the_api_contract(workflow, target, path, body):
    plan = MODULE.build_plan(workflow, target, None, MODULE.BASE_URL)
    request = plan["request"]

    assert request["method"] == "POST"
    assert request["url"] == f"{MODULE.BASE_URL}{path}"
    assert request["headers"]["Content-Type"] == "application/json"
    assert request["json"] == body


def test_mcp_plan_uses_streamable_http_instead_of_an_ad_hoc_body():
    plan = MODULE.build_plan("mcp", "find recent posts", None, MODULE.BASE_URL)

    assert plan["request"] == {
        "protocol": "mcp",
        "transport": "streamable-http",
        "url": "https://xquik.com/mcp",
        "headers": {"x-api-key": "$XQUIK_API_KEY"},
        "tools": ["explore", "xquik"],
        "task": "find recent posts",
    }


@pytest.mark.parametrize(
    ("workflow", "limit"),
    [("user", 1), ("search", 201), ("followers", 19), ("followers", 201)],
)
def test_invalid_limits_are_rejected(workflow, limit):
    with pytest.raises(ValueError):
        MODULE.validate_limit(workflow, limit)
