from literax.config import Settings

def test_settings_defaults():
    s = Settings(environment="development")
    assert not s.is_production
    assert not s.is_testing
    assert s.log_level == "INFO"

def test_settings_environment_flags():
    prod = Settings(environment="production")
    assert prod.is_production
    assert not prod.is_testing

    test_env = Settings(environment="testing")
    assert not test_env.is_production
    assert test_env.is_testing
