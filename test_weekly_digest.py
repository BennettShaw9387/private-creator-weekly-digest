import unittest

from weekly_digest import DigestRequest, prepare_digest


class DigestDecisionTest(unittest.TestCase):
    def test_only_subscribed_owners_receive_their_asset_names(self) -> None:
        request = DigestRequest.from_dict({
            "week": "2026-W38",
            "processed_titles": ["Transcript ready"],
            "assets": {"a1": "Course notes", "a2": "Audio pack"},
            "subscribers": [
                {"email": "ada@example.test", "subscribed": True, "asset_ids": ["a1"]},
                {"email": "ben@example.test", "subscribed": False, "asset_ids": ["a2"]},
                {"email": "cy@example.test", "subscribed": True, "asset_ids": []},
            ],
        })
        self.assertEqual(
            prepare_digest(request),
            [("ada@example.test", "Week 2026-W38\nYour digital assets:\nCourse notes\nProcessed this week:\nTranscript ready")],
        )


if __name__ == "__main__":
    unittest.main()
