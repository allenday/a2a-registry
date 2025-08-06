#!/usr/bin/env python3
"""Simple protobuf generation script for A2A Registry."""

import subprocess
import sys
import shutil
from pathlib import Path

# Get project root
project_root = Path(__file__).parent.parent
output_dir = project_root / "src" / "a2a_registry" / "proto" / "generated"

# Clean and create output directory
if output_dir.exists():
    shutil.rmtree(output_dir)
output_dir.mkdir(parents=True)

# Generate protobuf files
cmd = [
    sys.executable, "-m", "grpc_tools.protoc",
    "--proto_path=proto",
    "--proto_path=third_party/a2a/specification/grpc", 
    "--proto_path=third_party/api-common-protos",
    f"--python_out={output_dir}",
    f"--grpc_python_out={output_dir}",
    "proto/registry.proto",
    "third_party/a2a/specification/grpc/a2a.proto"
]

print(f"Running: {' '.join(cmd)}")
result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)

if result.returncode != 0:
    print(f"Error: {result.stderr}")
    sys.exit(1)

# Fix imports
registry_pb2 = output_dir / "registry_pb2.py"
if registry_pb2.exists():
    content = registry_pb2.read_text()
    content = content.replace("import a2a_pb2 as a2a__pb2", "from . import a2a_pb2 as a2a__pb2")
    registry_pb2.write_text(content)
    print("✅ Fixed registry_pb2.py imports")

# Fix grpc imports
registry_grpc = output_dir / "registry_pb2_grpc.py"
if registry_grpc.exists():
    content = registry_grpc.read_text()
    content = content.replace("import registry_pb2 as registry__pb2", "from . import registry_pb2 as registry__pb2")
    registry_grpc.write_text(content)
    print("✅ Fixed registry_pb2_grpc.py imports")

# Create proper __init__.py
init_content = '''"""Generated protobuf modules for A2A Registry."""

try:
    from . import a2a_pb2
    from . import registry_pb2
    from . import registry_pb2_grpc
    from . import a2a_pb2_grpc
except ImportError:
    pass

__all__ = ["a2a_pb2", "registry_pb2", "registry_pb2_grpc", "a2a_pb2_grpc"]
'''
(output_dir / "__init__.py").write_text(init_content)

print("✅ Protobuf generation completed!")
print("Generated files:")
for f in sorted(output_dir.glob("*.py")):
    print(f"  - {f.name}")