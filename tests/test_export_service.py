import csv
import io

from backend.services.export_service import export_matrix_to_csv


def test_empty_csv_keeps_same_audit_headers():
    empty_headers = next(csv.reader(io.StringIO(export_matrix_to_csv([]))))
    populated_headers = next(csv.reader(io.StringIO(
        export_matrix_to_csv([{"ejecucion_id": 1, "hash_prompt": "abc"}])
    )))
    populated_headers[0] = populated_headers[0].removeprefix("\ufeff")

    assert empty_headers == populated_headers
    assert "version_plantilla_prompt" in empty_headers
    assert "hash_prompt" in empty_headers
