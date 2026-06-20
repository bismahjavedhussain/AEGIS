"""AEGIS HuggingFace Spaces entry point.

HuggingFace Spaces looks for app.py at the project root.
"""

import os
import sys

# --- Compatibility hotfix for gradio 5.9.1 + pydantic v2 -------------------
# pydantic v2 emits JSON schemas where `additionalProperties` can be a bool.
# gradio_client's schema walker assumes dicts and crashes with
# "TypeError: argument of type 'bool' is not iterable". Patch it to treat any
# non-dict (bool) schema as "Any". Safe no-op once gradio is upgraded.
try:
    import gradio_client.utils as _gc_utils

    _orig_json_schema = _gc_utils._json_schema_to_python_type
    _orig_get_type = _gc_utils.get_type

    def _safe_json_schema(schema, defs=None):
        if isinstance(schema, bool):
            return "Any"
        return _orig_json_schema(schema, defs)

    def _safe_get_type(schema):
        if isinstance(schema, bool):
            return "Any"
        return _orig_get_type(schema)

    _gc_utils._json_schema_to_python_type = _safe_json_schema
    _gc_utils.get_type = _safe_get_type
except Exception as _e:  # pragma: no cover - defensive
    print(f"gradio_client hotfix skipped: {_e}", flush=True)
# ---------------------------------------------------------------------------

root = os.path.dirname(os.path.abspath(__file__))
aegis_dir = os.path.join(root, "aegis")
for d in [root, aegis_dir]:
    if d not in sys.path:
        sys.path.insert(0, d)

# Pre-warm: compile LangGraph before Gradio spawns worker threads
try:
    print("Pre-loading clinical knowledge base and compiling pipeline...", flush=True)
    from graph import aegis_graph  # noqa: F401 — compiles the graph
    print("Pipeline ready.", flush=True)
except Exception as e:
    print(f"Pipeline unavailable (simulation mode will be used): {e}", flush=True)

from ui.gradio_app import create_app

demo = create_app()

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
