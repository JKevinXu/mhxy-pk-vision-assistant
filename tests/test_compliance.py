from mhxy_pk_vision_assistant import check_feature_scope


def test_rejects_hidden_opponent_hp():
    decision = check_feature_scope("PK 时显示对方血量和真实血量")
    assert not decision.allowed


def test_allows_replay_estimation():
    decision = check_feature_scope("导入授权录像做复盘，基于公开可见事件估算血量区间")
    assert decision.allowed
