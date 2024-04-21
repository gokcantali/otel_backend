from typing import List
import csv
import io
import zipfile

from fastapi import Response

from otel_backend.ml.extract import Trace


async def get_csv(response: Response, TRACES: List[Trace], set_header=True):
    try:
        # Create a CSV string
        csv_data = io.StringIO()
        csv_writer = csv.writer(csv_data)
        csv_writer.writerow(['ip_source', 'ip_destination', 'is_anomaly',
                             'source_pod_label', 'source_namespace_label', 'source_port_label',
                             'destination_pod_label', 'destination_namespace_label', 'destination_port_label',
                             'ack_flag', 'psh_flag'])
        for trace in TRACES:
            csv_writer.writerow([
                trace.ip_source,
                trace.ip_destination,
                trace.is_anomaly,
                trace.labels.source_pod_label,
                trace.labels.source_namespace_label,
                trace.labels.source_port_label,
                trace.labels.destination_pod_label,
                trace.labels.destination_namespace_label,
                trace.labels.destination_port_label,
                trace.labels.ack_flag,
                trace.labels.psh_flag
            ])

        # Create a zip file containing the CSV
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("traces.csv", csv_data.getvalue())

        # Set response headers for download
        if set_header:
            response.headers["Content-Disposition"] = "attachment; filename=traces.zip"
            response.headers["Content-Type"] = "application/zip"

        # Return the zip file as a response
        return zip_buffer.getvalue()
    except Exception as e:
        return f"An error occurred: {e}\n"
