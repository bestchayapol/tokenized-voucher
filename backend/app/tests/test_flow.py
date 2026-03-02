import uuid

def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}

def register(client, email, password, role):
    r = client.post("/auth/register", json={"email": email, "password": password, "role": role})
    assert r.status_code == 200, r.text
    return r.json()

def login(client, email, password):
    r = client.post("/auth/login", data={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]

def test_e2e_issue_transfer_redeem_ledger(client):
    issuer = register(client, "issuer@mail.com", "secret", "issuer")
    user1  = register(client, "user1@mail.com", "secret", "user")
    user2  = register(client, "user2@mail.com", "secret", "user")
    merch  = register(client, "merchant@mail.com", "secret", "merchant")

    issuer_token = login(client, "issuer@mail.com", "secret")
    user1_token  = login(client, "user1@mail.com", "secret")

    # create voucher (issuer only)
    rv = client.post("/vouchers", json={"code": "FOOD-2026", "name": "Food Voucher 2026"}, headers=auth_headers(issuer_token))
    assert rv.status_code == 200, rv.text
    voucher_id = rv.json()["id"]

    # issue 100 to user1
    r_issue = client.post(f"/vouchers/{voucher_id}/issue", json={
        "to_user_id": user1["id"],
        "amount": 100,
        "ref_id": str(uuid.uuid4())
    }, headers=auth_headers(issuer_token))
    assert r_issue.status_code == 200, r_issue.text

    # transfer 30 from user1 -> user2
    r_transfer = client.post(f"/vouchers/{voucher_id}/transfer", json={
        "to_user_id": user2["id"],
        "amount": 30,
        "ref_id": str(uuid.uuid4())
    }, headers=auth_headers(user1_token))
    assert r_transfer.status_code == 200, r_transfer.text

    # redeem 50 from user1 -> merchant
    redeem_ref = str(uuid.uuid4())
    r_redeem = client.post(f"/vouchers/{voucher_id}/redeem", json={
        "merchant_user_id": merch["id"],
        "amount": 50,
        "ref_id": redeem_ref
    }, headers=auth_headers(user1_token))
    assert r_redeem.status_code == 200, r_redeem.text

    # idempotency: same ref_id again => 409
    r_redeem2 = client.post(f"/vouchers/{voucher_id}/redeem", json={
        "merchant_user_id": merch["id"],
        "amount": 50,
        "ref_id": redeem_ref
    }, headers=auth_headers(user1_token))
    assert r_redeem2.status_code == 409, r_redeem2.text

    # user1 balance should be 20 (100 - 30 - 50)
    r_bal = client.get(f"/vouchers/{voucher_id}/balance/me", headers=auth_headers(user1_token))
    assert r_bal.status_code == 200, r_bal.text
    assert r_bal.json()["balance"] == 20

    # ledger should have at least 3 events
    r_ledger = client.get(f"/ledger/vouchers/{voucher_id}?limit=20&offset=0", headers=auth_headers(user1_token))
    assert r_ledger.status_code == 200, r_ledger.text
    assert len(r_ledger.json()) >= 3

def test_role_forbidden_create_voucher(client):
    register(client, "issuer2@mail.com", "secret", "issuer")
    user = register(client, "normal@mail.com", "secret", "user")
    user_token = login(client, "normal@mail.com", "secret")

    r = client.post("/vouchers", json={"code": "X", "name": "X"}, headers=auth_headers(user_token))
    assert r.status_code in (403, 401), r.text

def test_insufficient_balance_transfer(client):
    issuer = register(client, "issuer3@mail.com", "secret", "issuer")
    u1 = register(client, "u1@mail.com", "secret", "user")
    u2 = register(client, "u2@mail.com", "secret", "user")

    issuer_token = login(client, "issuer3@mail.com", "secret")
    u1_token = login(client, "u1@mail.com", "secret")

    rv = client.post("/vouchers", json={"code": "TEST", "name": "Test"}, headers=auth_headers(issuer_token))
    voucher_id = rv.json()["id"]

    # try transfer without issue first
    r = client.post(f"/vouchers/{voucher_id}/transfer", json={
        "to_user_id": u2["id"],
        "amount": 10,
        "ref_id": str(uuid.uuid4())
    }, headers=auth_headers(u1_token))
    assert r.status_code == 400, r.text