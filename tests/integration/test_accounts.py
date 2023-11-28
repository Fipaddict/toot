import json

from toot import App, User, api, cli
from toot.entities import Account, Relationship, from_dict


def test_whoami(user: User, run):
    result = run(cli.whoami)
    assert result.exit_code == 0

    # TODO: test other fields once updating account is supported
    out = result.stdout.strip()
    assert f"@{user.username}" in out


def test_whoami_json(user: User, run):
    result = run(cli.whoami, "--json")
    assert result.exit_code == 0

    account = from_dict(Account, json.loads(result.stdout))
    assert account.username == user.username


def test_whois(app: App, friend: User, run):
    variants = [
        friend.username,
        f"@{friend.username}",
        f"{friend.username}@{app.instance}",
        f"@{friend.username}@{app.instance}",
    ]

    for username in variants:
        result = run(cli.whois, username)
        assert result.exit_code == 0
        assert f"@{friend.username}" in result.stdout


def test_following(app: App, user: User, friend: User, friend_id, run):
    # Make sure we're not initally following friend
    api.unfollow(app, user, friend_id)

    result = run(cli.following, user.username)
    assert result.exit_code == 0
    assert result.stdout.strip() == ""

    result = run(cli.follow, friend.username)
    assert result.exit_code == 0
    assert result.stdout.strip() == f"✓ You are now following {friend.username}"

    result = run(cli.following, user.username)
    assert result.exit_code == 0
    assert friend.username in result.stdout.strip()

    # If no account is given defaults to logged in user
    result = run(cli.following)
    assert result.exit_code == 0
    assert friend.username in result.stdout.strip()

    result = run(cli.unfollow, friend.username)
    assert result.exit_code == 0
    assert result.stdout.strip() == f"✓ You are no longer following {friend.username}"

    result = run(cli.following, user.username)
    assert result.exit_code == 0
    assert result.stdout.strip() == ""


def test_following_case_insensitive(user: User, friend: User, run):
    assert friend.username != friend.username.upper()
    result = run(cli.follow, friend.username.upper())
    assert result.exit_code == 0

    out = result.stdout.strip()
    assert out == f"✓ You are now following {friend.username.upper()}"


def test_following_not_found(run):
    result = run(cli.follow, "bananaman")
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: Account not found"

    result = run(cli.unfollow, "bananaman")
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: Account not found"


def test_following_json(app: App, user: User, friend: User, user_id, friend_id, run_json):
    # Make sure we're not initally following friend
    api.unfollow(app, user, friend_id)

    result = run_json(cli.following, user.username, "--json")
    assert result == []

    result = run_json(cli.followers, friend.username, "--json")
    assert result == []

    result = run_json(cli.follow, friend.username, "--json")
    relationship = from_dict(Relationship, result)
    assert relationship.id == friend_id
    assert relationship.following is True

    [result] = run_json(cli.following, user.username, "--json")
    relationship = from_dict(Relationship, result)
    assert relationship.id == friend_id

    # If no account is given defaults to logged in user
    [result] = run_json(cli.following, user.username, "--json")
    relationship = from_dict(Relationship, result)
    assert relationship.id == friend_id

    [result] = run_json(cli.followers, friend.username, "--json")
    assert result["id"] == user_id

    result = run_json(cli.unfollow, friend.username, "--json")
    assert result["id"] == friend_id
    assert result["following"] is False

    result = run_json(cli.following, user.username, "--json")
    assert result == []

    result = run_json(cli.followers, friend.username, "--json")
    assert result == []


def test_mute(app, user, friend, friend_id, run):
    # Make sure we're not initially muting friend
    api.unmute(app, user, friend_id)

    result = run(cli.muted)
    assert result.exit_code == 0

    out = result.stdout.strip()
    assert out == "No accounts muted"

    result = run(cli.mute, friend.username)
    assert result.exit_code == 0

    out = result.stdout.strip()
    assert out == f"✓ You have muted {friend.username}"

    result = run(cli.muted)
    assert result.exit_code == 0

    out = result.stdout.strip()
    assert friend.username in out

    result = run(cli.unmute, friend.username)
    assert result.exit_code == 0

    out = result.stdout.strip()
    assert out == f"✓ {friend.username} is no longer muted"

    result = run(cli.muted)
    assert result.exit_code == 0

    out = result.stdout.strip()
    assert out == "No accounts muted"


def test_mute_case_insensitive(friend: User, run):
    result = run(cli.mute, friend.username.upper())
    assert result.exit_code == 0

    out = result.stdout.strip()
    assert out == f"✓ You have muted {friend.username.upper()}"


def test_mute_not_found(run):
    result = run(cli.mute, "doesnotexistperson")
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: Account not found"

    result = run(cli.unmute, "doesnotexistperson")
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: Account not found"


def test_mute_json(app: App, user: User, friend: User, run_json, friend_id):
    # Make sure we're not initially muting friend
    api.unmute(app, user, friend_id)

    result = run_json(cli.muted, "--json")
    assert result == []

    result = run_json(cli.mute, friend.username, "--json")
    relationship = from_dict(Relationship, result)
    assert relationship.id == friend_id
    assert relationship.muting is True

    [result] = run_json(cli.muted, "--json")
    account = from_dict(Account, result)
    assert account.id == friend_id

    result = run_json(cli.unmute, friend.username, "--json")
    relationship = from_dict(Relationship, result)
    assert relationship.id == friend_id
    assert relationship.muting is False

    result = run_json(cli.muted, "--json")
    assert result == []


def test_block(app, user, friend, friend_id, run):
    # Make sure we're not initially blocking friend
    api.unblock(app, user, friend_id)

    result = run(cli.blocked)
    assert result.exit_code == 0

    out = result.stdout.strip()
    assert out == "No accounts blocked"

    result = run(cli.block, friend.username)
    assert result.exit_code == 0

    out = result.stdout.strip()
    assert out == f"✓ You are now blocking {friend.username}"

    result = run(cli.blocked)
    assert result.exit_code == 0

    out = result.stdout.strip()
    assert friend.username in out

    result = run(cli.unblock, friend.username)
    assert result.exit_code == 0

    out = result.stdout.strip()
    assert out == f"✓ {friend.username} is no longer blocked"

    result = run(cli.blocked)
    assert result.exit_code == 0

    out = result.stdout.strip()
    assert out == "No accounts blocked"


def test_block_case_insensitive(friend: User, run):
    result = run(cli.block, friend.username.upper())
    assert result.exit_code == 0

    out = result.stdout.strip()
    assert out == f"✓ You are now blocking {friend.username.upper()}"


def test_block_not_found(run):
    result = run(cli.block, "doesnotexistperson")
    assert result.exit_code == 1
    assert result.stderr.strip() == "Error: Account not found"


def test_block_json(app: App, user: User, friend: User, run_json, friend_id):
    # Make sure we're not initially blocking friend
    api.unblock(app, user, friend_id)

    result = run_json(cli.blocked, "--json")
    assert result == []

    result = run_json(cli.block, friend.username, "--json")
    relationship = from_dict(Relationship, result)
    assert relationship.id == friend_id
    assert relationship.blocking is True

    [result] = run_json(cli.blocked, "--json")
    account = from_dict(Account, result)
    assert account.id == friend_id

    result = run_json(cli.unblock, friend.username, "--json")
    relationship = from_dict(Relationship, result)
    assert relationship.id == friend_id
    assert relationship.blocking is False

    result = run_json(cli.blocked, "--json")
    assert result == []
