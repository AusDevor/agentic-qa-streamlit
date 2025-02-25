import subprocess
import tempfile

import pypandoc

def detect_doc_type(bytes):
    # Check if it's a ZIP file (which .docx files are)
    if bytes.startswith(b"\x50\x4b\x03\x04"):  # ZIP file header
        return "docx"
    return "doc"

def extract_doc(docx):
    doc_type = detect_doc_type(docx)
    with tempfile.NamedTemporaryFile(delete=True, suffix=f".{doc_type}") as temp_file:
        temp_file.write(docx)
        temp_file.flush()
        temp_file.seek(0)
        if doc_type == "doc":  # detect ms doc files
            try:
                result = subprocess.run(
                    ["antiword", temp_file.name],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                output = result.stdout
            except subprocess.CalledProcessError:
                raise Exception(
                    "Error: Make sure 'antiword' is installed. Run: sudo apt-get install antiword"
                )
            except Exception as e:
                raise Exception(f"Conversion failed: {str(e)}")
        else:
            output = pypandoc.convert_file(temp_file.name, "plain", format="docx")
    return output.strip()