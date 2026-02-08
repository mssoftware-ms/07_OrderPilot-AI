
try:
    import celpy
    print("celpy imported successfully")
except ImportError:
    print("celpy import failed")

try:
    from google.api_core import common_expression_language
    print("google.api_core CEL imported successfully")
except ImportError:
    print("google.api_core CEL import failed")

import sys
print(sys.path)
