import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

UNIVERSITIES = [
    "IIT Bombay",
    "IIT Delhi",
    "IIT Madras",
    "IIT Kharagpur",
    "IIT Roorkee",
    "BITS Pilani",
    "Delhi University (DU)",
    "Mumbai University (MU)",
    "Anna University",
    "Vellore Institute of Technology (VIT)",
    "SRM University",
    "NIT Trichy",
    "NIT Surathkal",
    "Christ University",
    "Manipal Academy of Higher Education (MAHE)",
    "Stanford University",
    "MIT",
    "Harvard University",
    "New York University (NYU)",
    "University of Oxford"
]


def allowed_file(filename):
    """Check if the uploaded file has a valid extension."""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config['ALLOWED_EXTENSIONS']

def save_uploaded_file(file, target_directory):
    """
    Saves an uploaded file to the specified target directory with a unique name.
    Returns the saved secure filename, or None if the file is invalid.
    """
    if file and allowed_file(file.filename):
        # Create directory if it doesn't exist
        os.makedirs(target_directory, exist_ok=True)
        
        # Generate unique filename to avoid overwrites
        original_filename = secure_filename(file.filename)
        ext = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        
        file_path = os.path.join(target_directory, unique_filename)
        file.save(file_path)
        return unique_filename
    return None
