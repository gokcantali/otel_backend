import multiprocessing as mp

import numpy as np
import pandas as pd
import torch

from inference.encoder import (
    boolean_string_to_int,
    ip_encoder,
    number_normalizer,
    string_encoder,
)
from sklearn.neighbors import kneighbors_graph
from torch_geometric.data import Data


def diversity_index(series):
    return series.nunique() / len(series) if len(series) > 0 else 0

def process_group(group, time_window="10s"):
    group = group.set_index("timestamp")
    result = group["destination_port_label"].rolling(window=time_window).apply(diversity_index)
    group["diversity_index"] = result.values
    group.reset_index(inplace=True)
    return group

def process_chunk(chunk, time_window):
    chunk_groups = chunk.groupby("ip_source")
    processed_groups = []
    for _, group in chunk_groups:
        processed_groups.append(process_group(group, time_window))
    return pd.concat(processed_groups)

def split_dataframe(df, num_chunks):
    chunk_size = len(df) // num_chunks
    chunks = [df.iloc[i * chunk_size:(i + 1) * chunk_size] for i in range(num_chunks)]
    return chunks

def construct_port_scan_label(df, use_diversity_index=True):
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df.sort_values(by=["timestamp"], inplace=True)
    if use_diversity_index:
        num_chunks = min([mp.cpu_count(), len(df)])
        chunks = split_dataframe(df, num_chunks)
        time_window = "10s"
        with mp.Pool(processes=num_chunks) as pool:
            results = pool.starmap(process_chunk, [(chunk, time_window) for chunk in chunks])
        df = pd.concat(results, ignore_index=True)
        df["diversity_index"] = df["diversity_index"].fillna(0)
        df = df.sample(frac=1).reset_index(drop=True)
    return df


def preprocess_X(df, use_diversity_index=True):
    X = df.drop(columns=["is_anomaly", "anomaly_class"])
    #X["timestamp"] = pd.to_datetime(X["timestamp"], utc=True)
    #X.sort_values(by=["ip_source", "timestamp"], inplace=True)

    encoder_map = {
        "ip_source": ip_encoder,
        "ip_destination": ip_encoder,
        "source_pod_label": string_encoder,
        "destination_pod_label": string_encoder,
        "source_namespace_label": string_encoder,
        "destination_namespace_label": string_encoder,
        "source_port_label": number_normalizer,
        "destination_port_label": number_normalizer,
        "ack_flag": boolean_string_to_int,
        "psh_flag": boolean_string_to_int
    }

    for column, encoder_function in encoder_map.items():
        X = encoder_function(X, column)
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0)
    #get_data_insights(X, "./results/data_insights.txt")
    #visualize_data(X, "./results")
    features = ["ack_flag", "psh_flag", "ip_source_part1",
                "ip_source_part2", "ip_source_part3", "ip_source_part4",
                "ip_source_part5", "ip_source_part6", "ip_source_part7",
                "ip_source_part8", "ip_destination_part1", "ip_destination_part2",
                "ip_destination_part3", "ip_destination_part4", "ip_destination_part5",
                "ip_destination_part6", "ip_destination_part7", "ip_destination_part8",
                "source_pod_label_normalized", "destination_pod_label_normalized",
                "source_namespace_label_normalized",
                "destination_namespace_label_normalized",
                "source_port_label_normalized", "destination_port_label_normalized"]
    if use_diversity_index:
        features.append("diversity_index")
    X = X[features]
    return X


def preprocess_y(df):
    return df["anomaly_class"]


def preprocess_df(df, use_diversity_index=True):
    df = construct_port_scan_label(df, use_diversity_index=use_diversity_index)
    df["is_anomaly"] = df["is_anomaly"].replace({"True": 1, "False": 0}).astype(int)
    X = preprocess_X(df, use_diversity_index=use_diversity_index)
    y = preprocess_y(df)
    return X, y


def create_knn_graph(X, k=5):
    A = kneighbors_graph(
        X.values, n_neighbors=k, mode="connectivity",
        include_self=True, n_jobs=-1)
    A = A.tocoo()
    row = A.row.astype(np.int64)
    col = A.col.astype(np.int64)
    edge_index = np.vstack([row, col])
    return torch.tensor(edge_index, dtype=torch.long)


def convert_to_graph(X, y):
    edge_index = create_knn_graph(X)
    data = Data(x=torch.tensor(X.values, dtype=torch.float),
                      edge_index=edge_index,
                      y=torch.tensor(y.values, dtype=torch.long))
    return data
