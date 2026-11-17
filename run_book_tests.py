# Runs one of the book's FreeCAD test files inside FreeCADCmd and writes the result as JSON.
#   set WQCAD_TEST_FILE=...\tests\TestPartMatrixTransform.py
#   set WQCAD_OUT=...\logs\TestPartMatrixTransform.json
#   FreeCADCmd.exe run_book_tests.py
# (FreeCADCmd would treat extra command-line arguments as files to open, hence the environment variables.)
import importlib.util
import json
import os
import sys
import unittest

path = os.environ["WQCAD_TEST_FILE"]
out = os.environ["WQCAD_OUT"]
sys.path.insert(0, os.path.dirname(path))
name = os.path.splitext(os.path.basename(path))[0]
spec = importlib.util.spec_from_file_location(name, path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
suite = unittest.defaultTestLoader.loadTestsFromModule(module)
result = unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)
rows = {}
for case, _ in result.failures:
    rows[case.id()] = "FAIL"
for case, _ in result.errors:
    rows[case.id()] = "ERROR"
for case, why in result.skipped:
    rows[case.id()] = "skipped: " + why
with open(out, "w", encoding="utf-8") as fh:
    json.dump({"module": name, "run": result.testsRun, "failures": len(result.failures),
               "errors": len(result.errors), "skipped": len(result.skipped),
               "ok": result.wasSuccessful(), "not_ok": rows}, fh, ensure_ascii=False, indent=1)
print("WQCAD", name, "ran", result.testsRun, "ok" if result.wasSuccessful() else "NOT OK")
