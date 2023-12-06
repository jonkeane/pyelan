import pytest
import os
import tempfile
from pathlib import Path

from pyelan.pyelan import *

TEST_DATA_DIR = Path(__file__).resolve().parent 

def test_tierset():
    tier_set = tierSet(file=TEST_DATA_DIR / "Letters.eaf")
    assert tier_set.media == ["pyelan/templates/480.mp4"]

    # now write it out to ensure we can reference
    dir = tempfile.gettempdir()
    out = tierSet.elanOut(tier_set, dest = os.path.join(dir, "test.eaf"))
    out.write(os.path.join(dir, "test.eaf"))
    assert os.path.exists(os.path.join(dir, "test.eaf"))

