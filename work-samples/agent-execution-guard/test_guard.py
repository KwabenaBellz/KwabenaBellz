"""Synthetic unit tests; zero network, payment or actual email interaction."""
import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from guard import Guard,FakeProvider


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory()
        self.dbfile=Path(self.tmp.name)/"test.sqlite"
        self.guard=Guard(self.dbfile)
        self.payload={"client":"Synthetic Corp","action":"test"}

    def tearDown(self):
        self.guard.close()
        self.tmp.cleanup()

    def proposed(self):
        self.guard.propose("action-1","fake_update",self.payload)

    def test_approval_required(self):
        self.proposed()
        provider=FakeProvider()
        self.assertEqual(self.guard.execute("action-1",provider)["blocked"],"approval_required")
        self.assertEqual(provider.calls,0)

    def test_retry_and_verified_receipt(self):
        self.proposed()
        self.guard.approve("action-1")
        provider=FakeProvider(failures=1)
        status=self.guard.execute("action-1",provider)
        self.assertEqual(status["state"],"completed")
        self.assertEqual(status["attempts"],2)
        self.assertEqual(len(provider.effects),1)

    def test_duplicate_replay_suppressed(self):
        self.proposed()
        self.guard.approve("action-1")
        provider=FakeProvider()
        self.guard.execute("action-1",provider)
        self.assertTrue(self.guard.execute("action-1",provider)["replay_suppressed"])
        self.assertEqual(provider.calls,1)

    def test_same_key_changed_payload_refused(self):
        self.proposed()
        with self.assertRaises(ValueError):
            self.guard.propose("action-1","fake_update",{"client":"different"})

    def test_restart_preserves_completed_action(self):
        self.proposed()
        self.guard.approve("action-1")
        provider=FakeProvider()
        self.guard.execute("action-1",provider)
        self.guard.close()
        self.guard=Guard(self.dbfile)
        self.assertTrue(self.guard.execute("action-1",provider)["replay_suppressed"])
        self.assertEqual(provider.calls,1)

    def test_exhausted_retry_is_explicit(self):
        self.proposed()
        self.guard.approve("action-1")
        provider=FakeProvider(failures=10)
        self.assertEqual(self.guard.execute("action-1",provider,max_attempts=2)["state"],"retry_exhausted")
        self.assertEqual(len(provider.effects),0)


if __name__=="__main__":
    unittest.main()
