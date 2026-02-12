from typing import Iterable
from hashlib import md5

from answer_gen.exceptions import FileReadError
from io import BytesIO

def get_document_text(doc_content : BytesIO | bytes) -> Iterable[str]:
    # Keep pypdf as a soft dependency for modules that only need hashing.
    from pypdf import PdfReader

    if isinstance(doc_content, bytes):
        doc_content = BytesIO(doc_content)

    try:
        reader = PdfReader(doc_content)
    except:
        raise FileReadError('Unable to read document content')

    for i, page in enumerate(reader.pages):
        yield i, page.extract_text()


def get_document_hash(document : bytes) -> str:
    return md5(document).hexdigest()
