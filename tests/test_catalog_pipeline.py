import tempfile
from pathlib import Path
import unittest

import numpy as np

from laut.catalog import Catalog
from laut.pipeline import run_manifest


class CatalogPipelineTest(unittest.TestCase):
    def test_npz_catalog_and_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            np.savez(root / "model.npz", temperature=np.array([1.0, 2.0, 3.0]))
            np.savez(root / "reference.npz", temperature=np.array([1.0, 2.0, 2.0]))
            (root / "catalog.toml").write_text(
                """
[[sources]]
id = "model"
driver = "npz"
uri = "model.npz"
variables = {sst = "temperature"}

[[sources]]
id = "reference"
driver = "npz"
uri = "reference.npz"
variables = {sst = "temperature"}
""".strip(),
                encoding="utf-8",
            )
            (root / "run.toml").write_text(
                """
catalog = "catalog.toml"
output_dir = "out"

[[configurations]]
id = "candidate"
stage = "S4"

[[evaluations]]
configuration = "candidate"
criterion_id = "O2_SST_RMSE"
model_source = "model"
reference_source = "reference"
variable = "sst"
""".strip(),
                encoding="utf-8",
            )
            catalog = Catalog.from_toml(root / "catalog.toml")
            self.assertEqual(catalog.validate(), [])
            result = run_manifest(root / "run.toml")
            self.assertEqual(len(result.comparison.records), 1)
            self.assertAlmostEqual(result.comparison.records[0].value, np.sqrt(1.0 / 3.0))
            self.assertFalse(result.comparison.scores[0].accepted)


if __name__ == "__main__":
    unittest.main()

