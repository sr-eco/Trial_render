from pathlib import Path
import os
import sys

# ✅ Set project root dynamically
project_root = Path(__file__).resolve().parent

# ✅ Ensure the project runs from the root directory
os.chdir(project_root)
sys.path.insert(0, str(project_root))

# ✅ Define paths dynamically
data_folder = project_root / "data"
utils_folder = project_root / "utils"
log_file = project_root / "logs" / "app.log"
output_folder = project_root / "Output"  # ✅ Add Output folder

# ✅ Ensure necessary folders exist
for folder in [data_folder, utils_folder, project_root / "logs", output_folder]:
    folder.mkdir(parents=True, exist_ok=True)

print(f"✅ Project root: {project_root}")
print(f"📂 Data folder: {data_folder}")
print(f"📂 Output folder: {output_folder}")
print(f"📄 Log file: {log_file}")


DEFAULT_YEAR = 2001