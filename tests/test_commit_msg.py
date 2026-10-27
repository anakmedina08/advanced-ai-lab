import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_commit_msg import is_valid, main  # noqa: E402


@pytest.mark.parametrize(
    "msg",
    [
        "feat(scraping): descubre URLs desde el sitemap",
        "fix: corrige umbral",
        "docs!: cambia ADR",
        'Revert "feat: x"',
    ],
)
def test_accepts_semantic_messages(msg):
    assert is_valid(msg)


@pytest.mark.parametrize("msg", ["cambios varios", "Feat: x", "feat:sin espacio", "wip"])
def test_rejects_free_text(msg):
    assert not is_valid(msg)


def test_main_reads_git_message_file(tmp_path):
    f = tmp_path / "COMMIT_EDITMSG"
    f.write_text("chore: inicial\n\ncuerpo")
    assert main(["hook", str(f)]) == 0
