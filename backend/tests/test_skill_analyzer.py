# ======================================================================
# PART C (Phase 8): three student profiles at engine level
# ======================================================================
STUDENT_A = {skill_id: 1 for skill_id in PRIYA}
STUDENT_B = {
    "html": 4, "css": 4, "javascript": 3, "git": 3, "react": 2,
    "sql": 3, "node": 2, "rest": 3, "auth": 2, "testing": 3,
}
STUDENT_C = {
    "html": 5, "css": 4, "javascript": 4, "git": 3, "react": 4,
    "sql": 3, "node": 3, "rest": 3, "auth": 3, "testing": 3,
}


@pytest.mark.parametrize(
    "ratings, earned, readiness, achieved, improve, gaps",
    [
        (STUDENT_A, 10, 29, 0, 0, 10),  # beginner: every skill is 2+ levels away
        (STUDENT_B, 29, 83, 5, 4, 1),   # intermediate: only React is far away
        (STUDENT_C, 34, 97, 9, 1, 0),   # advanced: only REST APIs is 1 level away (HTML 5 is capped at 4)
    ],
    ids=["A-beginner", "B-intermediate", "C-advanced"],
)
def test_three_student_profiles(ratings, earned, readiness, achieved, improve, gaps):
    result = analyze_skill_gap(FULL_STACK, ratings)
    assert result["points_possible"] == 35
    assert result["points_earned"] == earned
    assert result["readiness_score"] == readiness
    assert (result["achieved_count"], result["needs_improvement_count"], result["skill_gap_count"]) == (
        achieved, improve, gaps,
    )


def test_gap_counts_always_add_up():
    for ratings in (STUDENT_A, STUDENT_B, STUDENT_C, PRIYA, {}):
        result = analyze_skill_gap(FULL_STACK, ratings)
        assert (
            result["achieved_count"] + result["needs_improvement_count"] + result["skill_gap_count"]
            == result["total_skills"]
            == 10
        )
        assert 0 <= result["readiness_score"] <= 100