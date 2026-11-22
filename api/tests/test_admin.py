"""Tests for is_admin (BE-065)."""

import pytest

from app.principal import Machine, User, is_admin
from app.settings import Settings

ADMIN_IDS = ("user_abc", "user_xyz")


class TestIsAdminPure:
    """is_admin is a pure function: give it the ids, it gives a bool."""

    def test_user_in_list_is_admin(self) -> None:
        user = User(user_id="user_abc")
        assert is_admin(user, ADMIN_IDS) is True

    def test_user_not_in_list_is_not_admin(self) -> None:
        user = User(user_id="user_unknown")
        assert is_admin(user, ADMIN_IDS) is False

    def test_machine_is_never_admin(self) -> None:
        # Even when its key_label equals a listed ID
        machine = Machine(key_label="user_abc")
        assert is_admin(machine, ADMIN_IDS) is False

    def test_empty_list_means_no_admins(self) -> None:
        user = User(user_id="user_abc")
        assert is_admin(user, ()) is False


class TestSettingsAdminUserIds:
    """admin_user_ids is optional; an empty value does not stop the app."""

    def test_app_starts_without_admin_user_ids(self) -> None:
        settings = Settings(
            _env_file=None,
            api_keys="test-key",
            admin_user_ids="",
        )
        # The attribute exists and is empty
        assert settings.admin_user_ids == ""

    def test_app_starts_with_admin_user_ids(self) -> None:
        settings = Settings(
            _env_file=None,
            api_keys="test-key",
            admin_user_ids="user_abc, user_xyz",
        )
        assert settings.admin_user_ids == "user_abc, user_xyz"
