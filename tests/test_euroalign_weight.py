"""CPU-only checks. CUDA Qwen3-14B execution requires an external GPU runner."""
import importlib.util
import unittest

from eurobiasbench.euroalign_weight import get_down_proj


class OfflineChecks(unittest.TestCase):
    def test_code_is_importable_without_torch(self):
        import eurobiasbench.euroalign_weight as weight
        self.assertTrue(callable(weight.create_patch))

    @unittest.skipUnless(importlib.util.find_spec("torch"), "Torch not installed in lightweight CI")
    def test_rank_one_edit_and_exact_restoration_with_toy_model(self):
        import torch
        from eurobiasbench.euroalign_weight import apply_patch

        class Toy:
            def __init__(self):
                self.mlp = type("MLP", (), {"down_proj": torch.nn.Linear(3, 2, bias=False)})()

        class Model:
            def __init__(self):
                self.model = type("Wrapper", (), {"layers": [Toy()] * 4})()

        model = Model()
        weight = model.model.layers[-1].mlp.down_proj.weight
        original = weight.detach().clone()
        u = torch.tensor([1.0, -2.0])
        v = torch.tensor([0.05, 0.08, -0.01])
        with apply_patch(model, 3, u, v) as metadata:
            self.assertGreater(metadata["modified_elements"], 0)
            expected = original + torch.outer(u, v)
            self.assertTrue(torch.allclose(weight, expected, atol=1e-5))
        self.assertTrue(torch.equal(weight, original))


if __name__ == "__main__":
    unittest.main()
