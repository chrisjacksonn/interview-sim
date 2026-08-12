"""Request Budget hidden suite.

Never copied into a session workspace.

Weighted toward the two rules a working-looking solution usually gets wrong: the
boundary is half-open, so an event at exactly at - window has gone, and a refused
request must leave no trace, or a client who hits the limit once stays limited
forever.
"""

import unittest

from solution import RateLimiter


class TestBasics(unittest.TestCase):
    def test_first_request_is_allowed(self):
        self.assertIs(RateLimiter(1, 10).allow("a", 0), True)

    def test_up_to_the_limit(self):
        limiter = RateLimiter(3, 10)
        self.assertIs(limiter.allow("a", 0), True)
        self.assertIs(limiter.allow("a", 1), True)
        self.assertIs(limiter.allow("a", 2), True)

    def test_one_past_the_limit_is_refused(self):
        limiter = RateLimiter(3, 10)
        for moment in (0, 1, 2):
            limiter.allow("a", moment)
        self.assertIs(limiter.allow("a", 3), False)

    def test_returns_actual_booleans(self):
        limiter = RateLimiter(1, 10)
        self.assertIsInstance(limiter.allow("a", 0), bool)
        self.assertIsInstance(limiter.allow("a", 1), bool)

    def test_limit_of_one(self):
        limiter = RateLimiter(1, 5)
        self.assertIs(limiter.allow("a", 0), True)
        self.assertIs(limiter.allow("a", 4), False)
        self.assertIs(limiter.allow("a", 5), True)

    def test_several_requests_can_share_a_timestamp(self):
        limiter = RateLimiter(2, 10)
        self.assertIs(limiter.allow("a", 7), True)
        self.assertIs(limiter.allow("a", 7), True)
        self.assertIs(limiter.allow("a", 7), False)

    # --- the boundary ---

    def test_an_event_exactly_a_window_old_has_expired(self):
        limiter = RateLimiter(1, 10)
        limiter.allow("a", 0)
        self.assertIs(limiter.allow("a", 10), True)

    def test_a_moment_before_the_boundary_still_counts(self):
        limiter = RateLimiter(1, 10)
        limiter.allow("a", 0)
        self.assertIs(limiter.allow("a", 9.999), False)

    def test_the_window_slides_rather_than_resetting(self):
        """A fixed bucket would let four through in a ten second span."""
        limiter = RateLimiter(2, 10)
        self.assertIs(limiter.allow("a", 8), True)
        self.assertIs(limiter.allow("a", 9), True)
        self.assertIs(limiter.allow("a", 11), False)
        self.assertIs(limiter.allow("a", 18), True)

    def test_a_long_gap_clears_everything(self):
        limiter = RateLimiter(2, 10)
        limiter.allow("a", 0)
        limiter.allow("a", 1)
        self.assertIs(limiter.allow("a", 1000), True)
        self.assertEqual(limiter.count("a", 1000), 1)

    # --- a refusal leaves no trace ---

    def test_a_refusal_does_not_fill_the_budget(self):
        """The one that turns a brief burst into a permanent ban."""
        limiter = RateLimiter(1, 10)
        limiter.allow("a", 0)
        for moment in (1, 2, 3, 4, 5, 6, 7, 8, 9):
            self.assertIs(limiter.allow("a", moment), False)
        self.assertIs(limiter.allow("a", 10), True)

    def test_refusals_do_not_show_up_in_the_count(self):
        limiter = RateLimiter(1, 10)
        limiter.allow("a", 0)
        limiter.allow("a", 1)
        limiter.allow("a", 2)
        self.assertEqual(limiter.count("a", 3), 1)

    def test_hammering_does_not_delay_recovery(self):
        limiter = RateLimiter(2, 10)
        limiter.allow("a", 0)
        limiter.allow("a", 0)
        for moment in range(1, 10):
            limiter.allow("a", moment)
        self.assertIs(limiter.allow("a", 10), True)

    # --- counting ---

    def test_count_of_an_unseen_client(self):
        self.assertEqual(RateLimiter(3, 5).count("nobody", 100), 0)

    def test_count_expires_with_the_window(self):
        limiter = RateLimiter(3, 10)
        limiter.allow("a", 0)
        limiter.allow("a", 5)
        self.assertEqual(limiter.count("a", 9), 2)   # (-1, 9]  holds 0 and 5
        self.assertEqual(limiter.count("a", 10), 1)  # (0, 10]  drops 0
        self.assertEqual(limiter.count("a", 14), 1)  # (4, 14]  still holds 5
        self.assertEqual(limiter.count("a", 15), 0)  # (5, 15]  drops 5 too

    def test_count_does_not_itself_allow_anything(self):
        limiter = RateLimiter(1, 10)
        limiter.count("a", 0)
        limiter.count("a", 1)
        self.assertIs(limiter.allow("a", 2), True)

    def test_count_never_exceeds_the_limit(self):
        limiter = RateLimiter(2, 10)
        for moment in range(20):
            limiter.allow("a", moment * 0.1)
        self.assertLessEqual(limiter.count("a", 2), 2)

    # --- clients are separate ---

    def test_two_clients_do_not_share_a_budget(self):
        limiter = RateLimiter(1, 10)
        self.assertIs(limiter.allow("alice", 0), True)
        self.assertIs(limiter.allow("bob", 0), True)
        self.assertIs(limiter.allow("carol", 0), True)

    def test_one_client_filling_up_does_not_limit_another(self):
        limiter = RateLimiter(2, 10)
        limiter.allow("alice", 0)
        limiter.allow("alice", 1)
        self.assertIs(limiter.allow("alice", 2), False)
        self.assertIs(limiter.allow("bob", 2), True)
        self.assertIs(limiter.allow("bob", 3), True)
        self.assertIs(limiter.allow("bob", 4), False)

    def test_counts_are_per_client(self):
        limiter = RateLimiter(5, 10)
        limiter.allow("alice", 0)
        limiter.allow("alice", 1)
        limiter.allow("bob", 1)
        self.assertEqual(limiter.count("alice", 2), 2)
        self.assertEqual(limiter.count("bob", 2), 1)

    def test_keys_are_case_sensitive(self):
        limiter = RateLimiter(1, 10)
        self.assertIs(limiter.allow("Alice", 0), True)
        self.assertIs(limiter.allow("alice", 0), True)

    # --- odd input ---

    def test_an_empty_key_is_refused_without_raising(self):
        limiter = RateLimiter(5, 10)
        self.assertIs(limiter.allow("", 0), False)
        self.assertEqual(limiter.count("", 0), 0)

    def test_an_empty_key_does_not_consume_anyone_else_s_budget(self):
        limiter = RateLimiter(1, 10)
        limiter.allow("", 0)
        self.assertIs(limiter.allow("a", 0), True)

    def test_negative_times(self):
        limiter = RateLimiter(2, 10)
        self.assertIs(limiter.allow("a", -100), True)
        self.assertIs(limiter.allow("a", -95), True)
        self.assertIs(limiter.allow("a", -94), False)
        self.assertIs(limiter.allow("a", -90), True)

    def test_float_times(self):
        limiter = RateLimiter(2, 1)
        self.assertIs(limiter.allow("a", 0.1), True)
        self.assertIs(limiter.allow("a", 0.5), True)
        self.assertIs(limiter.allow("a", 0.9), False)
        self.assertIs(limiter.allow("a", 1.1), True)

    def test_a_bad_limit_raises(self):
        with self.assertRaises(ValueError):
            RateLimiter(0, 10)

    def test_a_negative_limit_raises(self):
        with self.assertRaises(ValueError):
            RateLimiter(-1, 10)

    def test_a_bad_window_raises(self):
        with self.assertRaises(ValueError):
            RateLimiter(2, 0)

    def test_a_negative_window_raises(self):
        with self.assertRaises(ValueError):
            RateLimiter(2, -5)

    # --- scale ---

    def test_a_long_run_stays_correct(self):
        limiter = RateLimiter(3, 5)
        allowed = 0
        for moment in range(20000):
            if limiter.allow("a", moment * 0.1):
                allowed += 1
        # 0.1s apart with a 5s window is 50 slots per window, and only 3 of any
        # 50 get through, so this lands far below the request count.
        self.assertLess(allowed, 2000)
        self.assertGreater(allowed, 900)

    def test_many_clients(self):
        limiter = RateLimiter(1, 10)
        for index in range(5000):
            self.assertIs(limiter.allow("client-%d" % index, 0), True)
        for index in range(5000):
            self.assertIs(limiter.allow("client-%d" % index, 5), False)

    def test_history_does_not_grow_without_bound(self):
        """Rescanning everything is the shape that dies here."""
        limiter = RateLimiter(2, 1)
        for moment in range(100000):
            limiter.allow("a", moment)
        self.assertEqual(limiter.count("a", 99999), 1)


if __name__ == "__main__":
    unittest.main()
