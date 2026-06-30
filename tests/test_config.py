import pytest
from config import Config


def test_config_creation():
    config = Config(
        db_name="testdb",
        db_user="user",
        db_pass="pass",
        db_host="localhost",
        db_port="5432",
        db_bk_name="backup",
        db_state=True,
        db_drive=False,
        db_time="00:00:00",
        db_time2="23:59:00",
        state_doc=True,
        state_anul=False,
        state_ncredi=False,
        state_nventas=False,
        state_guia=False,
        date_header="2025-01-01",
        debug=False,
        api_ssl_verify=False,
    )
    assert config.db_name == "testdb"
    assert config.db_port == "5432"
    assert config.state_doc is True
    assert config.debug is False
    assert config.api_ssl_verify is False


def test_config_boolean_fields():
    config = Config(
        db_name="testdb", db_user="user", db_pass="pass",
        db_host="localhost", db_port="5432", db_bk_name="backup",
        db_state=False, db_drive=True, db_time="00:00:00",
        db_time2="23:59:00", state_doc=True, state_anul=True,
        state_ncredi=True, state_nventas=True, state_guia=True,
        date_header="2025-01-01", debug=True, api_ssl_verify=True,
    )
    assert config.db_state is False
    assert config.db_drive is True
    assert config.state_doc is True
    assert config.state_anul is True
    assert config.debug is True
    assert config.api_ssl_verify is True
