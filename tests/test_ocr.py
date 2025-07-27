import simplejson as json


def compare_docs(doc1, doc2):
    """Compare two processed PDF documents for equality."""
    for page1, page2 in zip(doc1, doc2, strict=True):
        for block1, block2 in zip(page1, page2, strict=True):
            for line1, line2 in zip(block1, block2, strict=True):
                if line1.text != line2.text:
                    return False
            if block1.block_type != block2.block_type:
                return False
    return True


def test_local_process(index, sample_docket_id1):
    """Test process method, loading pdf from path."""
    from docketanalyzer.ocr import pdf_document

    manager = index[sample_docket_id1]
    pdf_path = manager.get_pdf_path(entry_number=1)
    ocr_path = manager.get_ocr_path(entry_number=1)
    ocr_data = json.loads(ocr_path.read_text())

    # Sample doc for comparison
    doc1 = pdf_document(pdf_path, load=ocr_data)

    # Doc to process from path
    doc2 = pdf_document(pdf_path).process()

    assert len(doc1) == len(doc2), "Document lengths do not match"
    assert compare_docs(doc1, doc2), "Processed documents are not equal"

    edited_ocr_data = ocr_data.copy()
    edited_ocr_data["pages"][0]["blocks"][0]["lines"][0]["content"] = "Edited text"
    doc3 = pdf_document(pdf_path, load=edited_ocr_data)
    assert not compare_docs(doc1, doc3), "Edited documents should not be equal"


def test_local_stream(index, sample_docket_id1):
    """Test stream method, loading pdf from bytes."""
    from docketanalyzer.ocr import pdf_document

    manager = index[sample_docket_id1]
    pdf_path = manager.get_pdf_path(entry_number=1)
    ocr_path = manager.get_ocr_path(entry_number=1)
    ocr_data = json.loads(ocr_path.read_text())

    # Sample doc for comparison
    doc1 = pdf_document(pdf_path, load=ocr_data)

    # Doc to process from path
    doc2 = pdf_document(pdf_path.read_bytes())
    for _ in doc2.stream():
        pass

    assert len(doc1) == len(doc2), "Document lengths do not match"
    assert compare_docs(doc1, doc2), "Processed documents are not equal"
