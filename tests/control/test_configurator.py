"""B-DAC1..3: configurator serialiser, frozen encoders and shared heads (CPU, mock).

ENGINEERING ONLY.  Scripted trees and a hashing mock encoder exercise the
pipeline; the Kev and CLM slots are checked to refuse without a binding and
never to touch the network.  No assertion here is about timing performance.
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiment_scaffold/src"))
sys.path.insert(0, str(ROOT / "experiments/paper_b"))

from causal_branch.control.configurator import (  # noqa: E402
    CLMBinding,
    CLMEncoder,
    ConfiguratorError,
    DecisionHistory,
    EmbeddingCache,
    EmbeddingProjector,
    EncoderUnavailable,
    HistoryEvent,
    KevBinding,
    KevEncoder,
    MockEncoder,
    SerialiserError,
    evaluate_with_configurator,
    fit_feature_map,
    serialise,
    serialise_root,
)
from causal_branch.control.configurator.encoder import (  # noqa: E402
    KEV_QUESTIONS_DRAFT,
    fingerprint_digest,
)
from configurator_scripted import scripted_population, split_by_family  # noqa: E402


def _hist(phase=1, step=3, n_extra=0, redact=()):
    ev = [HistoryEvent(0, "task", "fit a classifier for root R7"),
          HistoryEvent(1, "tool_call", "fit dev batch", name="fit"),
          HistoryEvent(2, "tool_result", "dev accuracy high", name="fit")]
    ev += [HistoryEvent(3, "assistant", f"note {i} " + "x" * 50) for i in range(n_extra)]
    return DecisionHistory(phase=phase, checkpoint_step=step, events=tuple(ev), redact=redact)


class SerialiserTests(unittest.TestCase):
    def test_rejects_non_visible_kind(self):
        with self.assertRaises(SerialiserError):
            HistoryEvent(1, "grade", "U=0.9")
        with self.assertRaises(SerialiserError):
            HistoryEvent(1, "outcome", "hidden accuracy 0.8")

    def test_rejects_post_decision_events(self):
        with self.assertRaises(SerialiserError):
            DecisionHistory(phase=1, checkpoint_step=1,
                            events=(HistoryEvent(0, "task", "t"), HistoryEvent(2, "assistant", "late")))

    def test_requires_task_statement(self):
        with self.assertRaises(SerialiserError):
            DecisionHistory(phase=1, checkpoint_step=1, events=(HistoryEvent(0, "assistant", "a"),))

    def test_redaction_and_determinism(self):
        h = _hist(redact=("R7",))
        a, b = serialise(h), serialise(h)
        self.assertEqual(a.sha256, b.sha256)
        self.assertNotIn("R7", a.text)
        self.assertIn("<id>", a.text)

    def test_truncation_keeps_task_and_recent_events(self):
        h = DecisionHistory(
            phase=1, checkpoint_step=200,
            events=tuple([HistoryEvent(0, "task", "TASKSTATEMENT")]
                         + [HistoryEvent(i, "assistant", f"event{i:03d} " + "y" * 80)
                            for i in range(1, 200)]))
        s = serialise(h, max_chars=2000, task_chars=200)
        self.assertTrue(s.truncated)
        self.assertLessEqual(len(s.text), 2000)
        self.assertIn("TASKSTATEMENT", s.text)
        self.assertIn("event199", s.text)
        self.assertNotIn("event001", s.text)
        self.assertIn("earlier events omitted", s.text)

    def test_h2_must_extend_h1(self):
        h1 = _hist(phase=1, step=2)
        good = DecisionHistory(phase=2, checkpoint_step=4,
                               events=h1.events + (HistoryEvent(4, "observation", "batch 2"),))
        serialise_root(h1, good)
        transplanted = DecisionHistory(
            phase=2, checkpoint_step=4,
            events=(HistoryEvent(0, "task", "fit a classifier for root R7"),
                    HistoryEvent(1, "tool_call", "a different branch", name="fit"),
                    HistoryEvent(4, "observation", "batch 2")))
        with self.assertRaises(SerialiserError):
            serialise_root(h1, transplanted)


class EncoderTests(unittest.TestCase):
    def test_mock_is_deterministic_and_normalised(self):
        e = MockEncoder(dim=32)
        x = e.embed(["alpha beta", "alpha beta", "gamma"])
        np.testing.assert_allclose(x[0], x[1])
        np.testing.assert_allclose(np.linalg.norm(x, axis=1), 1.0, atol=1e-9)
        self.assertEqual(x.shape, (3, 32))

    def test_clm_refuses_without_binding_and_never_calls_network(self):
        with mock.patch("urllib.request.urlopen", side_effect=AssertionError("network")):
            with self.assertRaises(EncoderUnavailable):
                CLMEncoder(CLMBinding()).embed(["x"])
            bound = CLMBinding(backbone_revision="abc", url="http://h/v1/embeddings",
                               head_path="/nope.pt", head_sha256="00")
            with self.assertRaises(EncoderUnavailable):
                CLMEncoder(bound).embed(["x"])      # allow_network defaults to False
            with self.assertRaises(EncoderUnavailable):
                CLMEncoder(CLMBinding(backbone_revision="abc", url="u"),
                           variant="clm_state_head", allow_network=True).embed(["x"])

    def test_clm_fingerprint_tracks_artifacts_not_url(self):
        a = CLMEncoder(CLMBinding(backbone_revision="r1", url="http://a"))
        b = CLMEncoder(CLMBinding(backbone_revision="r1", url="http://b"))
        c = CLMEncoder(CLMBinding(backbone_revision="r2", url="http://a"))
        d = CLMEncoder(CLMBinding(backbone_revision="r1", url="http://a"), variant="backbone_raw")
        self.assertEqual(fingerprint_digest(a.fingerprint()), fingerprint_digest(b.fingerprint()))
        self.assertNotEqual(fingerprint_digest(a.fingerprint()), fingerprint_digest(c.fingerprint()))
        self.assertNotEqual(fingerprint_digest(a.fingerprint()), fingerprint_digest(d.fingerprint()))

    def test_kev_refuses_without_binding_and_never_calls_network(self):
        with mock.patch("urllib.request.urlopen", side_effect=AssertionError("network")):
            with self.assertRaises(EncoderUnavailable):
                KevEncoder(KevBinding()).embed(["x"])
            with self.assertRaises(EncoderUnavailable):
                KevEncoder(KevBinding(revision="r", url="u", backend="mlx")).embed(["x"])

    def test_kev_parses_systemone_answers_via_fake_transport(self):
        seen = []

        def fake(body):
            seen.append(body)
            return {"answers": {
                "candidate_stale": {"type": "noul", "noul": 0.8},
                "shift_suspected": {"type": "noul", "noul": 0.1},
                "candidate_quality": {"type": "score", "score": 1.5},
                "verification_gain": {"type": "score", "score": 0.0},
                "progress": {"type": "score", "score": 2.0}}}

        enc = KevEncoder(KevBinding(), transport=fake)
        x = enc.embed(["state one"])
        np.testing.assert_allclose(x[0], [0.8, 0.1, 0.75, 0.0, 1.0])
        self.assertEqual(seen[0]["state"], "state one")
        self.assertEqual(seen[0]["questions"], KEV_QUESTIONS_DRAFT)

    def test_kev_question_set_enters_fingerprint(self):
        a = KevEncoder(KevBinding(revision="r"))
        q = dict(KEV_QUESTIONS_DRAFT)
        q.pop("progress")
        b = KevEncoder(KevBinding(revision="r"), questions=q)
        self.assertNotEqual(fingerprint_digest(a.fingerprint()), fingerprint_digest(b.fingerprint()))
        self.assertEqual(b.dim, a.dim - 1)

    def test_cache_is_keyed_by_encoder_fingerprint(self):
        cache = EmbeddingCache()
        a, b = MockEncoder(dim=16), MockEncoder(dim=16, salt="other")
        xa = cache.embed(a, ["t1", "t2", "t1"])
        self.assertEqual(len(cache), 2)
        xb = cache.embed(b, ["t1"])
        self.assertEqual(len(cache), 3)
        self.assertFalse(np.allclose(xa[0], xb[0]))
        np.testing.assert_allclose(xa[0], xa[2])


class ProjectorTests(unittest.TestCase):
    def test_k_must_be_below_dev_count(self):
        x = np.random.default_rng(0).normal(size=(5, 10))
        with self.assertRaises(ConfiguratorError):
            EmbeddingProjector(k=5).fit(x)
        z = EmbeddingProjector(k=3).fit(x).transform(x)
        np.testing.assert_allclose(z.std(axis=0), 1.0, atol=1e-9)

    def test_standardize_keeps_dims(self):
        x = np.random.default_rng(1).uniform(size=(6, 4))
        p = EmbeddingProjector(mode="standardize").fit(x)
        self.assertEqual(p.k, 4)
        np.testing.assert_allclose(p.transform(x).mean(axis=0), 0.0, atol=1e-12)


class FeatureMapTests(unittest.TestCase):
    def setUp(self):
        self.rows, self.hist = scripted_population(n_families=12, roots_per_family=4, seed=3)
        self.dev, self.test = split_by_family(self.rows, 8)

    def test_projection_never_sees_test_texts(self):
        enc = MockEncoder(dim=48)
        f1 = fit_feature_map(self.dev, self.hist, enc, k=4)
        hist2 = dict(self.hist)
        for r in self.test:     # perturb every test history
            h1, h2 = hist2[r["root_id"]]
            extra = HistoryEvent(h1.checkpoint_step, "assistant", "perturbed test text")
            h1b = DecisionHistory(1, h1.checkpoint_step, h1.events + (extra,), h1.redact)
            h2b = (DecisionHistory(2, h2.checkpoint_step,
                                   h1b.events + h2.events[len(h1.events):], h2.redact)
                   if h2 is not None else None)
            hist2[r["root_id"]] = (h1b, h2b)
        f2 = fit_feature_map(self.dev, hist2, enc, k=4)
        self.assertEqual(f1.projector.digest(), f2.projector.digest())

    def test_h2_contains_h1_and_feature_sets(self):
        enc = MockEncoder(dim=48)
        for fs in ("telemetry", "embedding", "telemetry+embedding"):
            fmap = fit_feature_map(self.dev, self.hist, enc, feature_set=fs, k=4)
            out = fmap.apply(self.test, self.hist)
            for r in out:
                self.assertTrue(set(r["h1"]) <= set(r["h2"]))
            keys = set(out[0]["h1"])
            self.assertEqual("tel_q" in keys, fs != "embedding")
            self.assertEqual(any(k.startswith("e1_") for k in keys), fs != "telemetry")

    def test_reached_flag_must_match_histories(self):
        enc = MockEncoder(dim=48)
        r = next(r for r in self.dev if r["reached2"])
        bad = dict(self.hist)
        bad[r["root_id"]] = (self.hist[r["root_id"]][0], None)
        with self.assertRaises(ConfiguratorError):
            fit_feature_map(self.dev, bad, enc, k=4)

    def test_outcomes_never_in_texts(self):
        fmap = fit_feature_map(self.dev, self.hist, MockEncoder(dim=48), k=4)
        t1, t2 = fmap._texts(self.rows, self.hist)
        for r in self.rows:
            for text in [t1[r["root_id"]], t2.get(r["root_id"], "")]:
                self.assertNotIn(r["root_id"], text)
                self.assertNotIn(r["family"], text)
                self.assertNotIn(f"{r['u_now']:.3f}", text)


class EndToEndTests(unittest.TestCase):
    def test_evaluate_with_configurator_all_feature_sets(self):
        rows, hist = scripted_population(n_families=20, roots_per_family=4, seed=11)
        dev, test = split_by_family(rows, 12)
        for fs in ("telemetry", "embedding", "telemetry+embedding"):
            report, prov = evaluate_with_configurator(
                dev, test, hist, MockEncoder(dim=64), feature_set=fs, k=6, n_bootstrap=40)
            self.assertTrue(report.matching["matched_decision_class"])
            self.assertIn("proposed-myopic", report.contrasts)
            self.assertEqual(report.n_roots, len(test))
            self.assertEqual(prov["feature_set"], fs)
            self.assertTrue(set(prov["h1_keys"]) <= set(prov["h2_keys"]))

    def test_kev_slot_end_to_end_with_fake_transport(self):
        rows, hist = scripted_population(n_families=16, roots_per_family=4, seed=5)
        dev, test = split_by_family(rows, 10)

        def fake(body):   # a keyword "Kev" so the slot runs on CPU
            s = body["state"]
            return {"answers": {
                "candidate_stale": {"type": "noul", "noul": 0.9 if "drift" in s else 0.2},
                "shift_suspected": {"type": "noul", "noul": 0.9 if "shift" in s else 0.1},
                "candidate_quality": {"type": "score", "score": 2.0 if "high" in s else 0.5},
                "verification_gain": {"type": "score", "score": 1.0},
                "progress": {"type": "score", "score": 2.0 if "CHECKPOINT 2" in s else 1.0}}}

        report, prov = evaluate_with_configurator(
            dev, test, hist, KevEncoder(KevBinding(), transport=fake),
            feature_set="telemetry+embedding", projection="standardize", n_bootstrap=40)
        self.assertEqual(prov["projector_mode"], "standardize")
        self.assertEqual(prov["encoder"]["kind"], "kev")
        self.assertTrue(report.matching["matched_decision_class"])

    def test_family_overlap_rejected(self):
        rows, hist = scripted_population(n_families=8, roots_per_family=4, seed=2)
        with self.assertRaises(ConfiguratorError):
            evaluate_with_configurator(rows, rows[:4], hist, MockEncoder())


if __name__ == "__main__":
    unittest.main()
