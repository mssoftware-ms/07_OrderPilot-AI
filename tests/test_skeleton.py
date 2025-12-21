def test_skeleton_imports():
    import importlib
    assert importlib.import_module("src.ui.app")
    assert importlib.import_module("src.ai.openai_service")
