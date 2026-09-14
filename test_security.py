from security import hash_password, verify_password


def test_password_hashing_preserves_the_exact_password() -> None:
    password = "  yellow boats sail at sunrise  "

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != password
    assert first_hash != second_hash
    assert verify_password(password, first_hash)
    assert verify_password(password, second_hash)
    assert not verify_password(password.strip(), first_hash)
    assert not verify_password("a different password entirely", first_hash)