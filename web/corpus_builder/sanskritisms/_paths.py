import os

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS_BUILDER_DIR = os.path.dirname(HERE)
WEB_DIR = os.path.dirname(CORPUS_BUILDER_DIR)
REPO_ROOT = os.path.dirname(WEB_DIR)
JSONL_DIR = os.path.join(CORPUS_BUILDER_DIR, 'jsonl')
DIPLOM_DIR = os.path.join(REPO_ROOT, 'nkrya-parallel', 'diplom-rubanova')


def diplom_path(name):
    return os.path.join(DIPLOM_DIR, name)
