import csv
import io
import os
import zipfile
from dataclasses import fields, is_dataclass
from typing import Any, List, Type

from fastapi import Response

from otel_backend.extract import Trace


def get_all_field_names(cls: Type[Any]) -> List[str]:
    """Recursively get all field names from the dataclass and nested dataclasses."""
    if not is_dataclass(cls):
        raise TypeError("The input must be a dataclass type")
    
    field_names = []
    for field in fields(cls):
        if is_dataclass(field.type):
            nested_fields = get_all_field_names(field.type)
            field_names.extend(nested_fields)
        else:
            field_names.append(field.name)
    return field_names

def get_all_values(obj: Any) -> List[str]:
    """Recursively get all values from the dataclass and nested dataclasses."""
    if not is_dataclass(obj):
        raise TypeError("The input object must be a dataclass instance")

    values = []
    for field in fields(obj.__class__):
        value = getattr(obj, field.name)
        if is_dataclass(value):
            nested_values = get_all_values(value)
            values.extend(nested_values)
        else:
            values.append(value)
    return values

def save_csv(TRACES: List[Trace]):
    os.makedirs('./data', exist_ok=True)
    file_path = './data/traces.csv'
    file_exists = os.path.exists(file_path)

    new_traces = []
    with open(file_path, 'a', newline='') as file:
        csv_writer = csv.writer(file)
        if TRACES:
            headers = get_all_field_names(TRACES[0].__class__)
            if not file_exists:
                # Write headers only if the file did not exist before
                csv_writer.writerow(headers)
            for trace in TRACES:
                values = get_all_values(trace)
                csv_writer.writerow(values)
                new_traces.append(dict(zip(headers, values)))

    return new_traces

async def get_csv_response(set_header=True) -> Any:
    file_path = './data/traces.csv'
    if not os.path.exists(file_path):
        return "File not found."

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        with open(file_path, 'r') as file:
            zip_file.writestr("traces.csv", file.read())

    if set_header:
        headers = {
            "Content-Disposition": "attachment; filename=traces.zip",
            "Content-Type": "application/zip"
        }
    else:
        headers = {}

    zip_buffer.seek(0)
    return Response(content=zip_buffer.getvalue(), headers=headers, media_type="application/zip")
