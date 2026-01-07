import argparse
import json
import math
from typing import List

import numpy as np
import pandas as pd
import torch
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModel

def mean_pool(last_hidden_state: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    # Mean-pool token embeddings with attention mask.
    mask = attention_mask.unsqueeze(-1).type_as(last_hidden_state)
    summed = torch.sum(last_hidden_state * mask, dim=1)
    counts = torch.clamp(mask.sum(dim=1), min=1e-9)
    return summed / counts

def cls_pool(last_hidden_state: torch.Tensor) -> torch.Tensor:
    # Take the [CLS] token embedding (index 0).
    return last_hidden_state[:, 0, :]

def embed_texts(
    texts: List[str],
    model_name: str = 'yiyanghkust/finbert-pretrain',
    pooling: str = 'mean',
    batch_size: int = 32,
    max_length: int = 128,
    device: str = None,
) -> np.ndarray:
    # Returns an array of shape [N, H] with embeddings.
    if device is None:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    model.to(device)
    model.eval()

    if pooling not in {'mean', 'cls'}:
        raise ValueError("pooling must be one of {'mean', 'cls'}")

    vecs = []

    use_autocast = device == 'cuda'
    num_batches = math.ceil(len(texts) / batch_size)
    for b in tqdm(range(num_batches), desc='Embedding'):
        batch = texts[b * batch_size : (b + 1) * batch_size]
        enc = tokenizer(batch, padding=True, truncation=True, max_length=max_length, return_tensors='pt')
        enc = {k: v.to(device) for k, v in enc.items()}

        if use_autocast:
            with torch.cuda.amp.autocast():
                out = model(**enc)
        else:
            out = model(**enc)

        last_hidden = out.last_hidden_state
        if pooling == 'mean':
            pooled = mean_pool(last_hidden, enc['attention_mask'])
        else:
            pooled = cls_pool(last_hidden)

        vecs.append(pooled.detach().cpu())

    return torch.cat(vecs, dim=0).numpy()

def main():
    ap = argparse.ArgumentParser(description='Embed tweets using FinBERT and save to CSV.')
    ap.add_argument('--in_csv', type=str, default = '../tweetProducer/stock_tweets_sorted.csv', help='Input CSV with tweets.')
    ap.add_argument('--text_col', type=str, default='Tweet', help='Column name containing tweet text.')
    ap.add_argument('--time_col', type=str, default=None, help='Optional timestamp column (kept if present).')
    ap.add_argument('--id_col', type=str, default=None, help='Optional id/ticker column (kept if present).')
    ap.add_argument('--model', type=str, default='yiyanghkust/finbert-pretrain', help='HF model name for FinBERT.')
    ap.add_argument('--pooling', type=str, default='mean', choices=['mean', 'cls'], help='Pooling strategy.')
    ap.add_argument('--batch_size', type=int, default=32, help='Batch size.')
    ap.add_argument('--max_length', type=int, default=128, help='Max tokens per tweet.')
    ap.add_argument('--out_csv', default='chronos_output/embedded_out.csv',type=str, help='Output CSV with embeddings.')
    ap.add_argument('--explode', action='store_true', help='Also create emb_0..emb_N columns.')
    args = ap.parse_args()

    df = pd.read_csv(args.in_csv)
    if args.text_col not in df.columns:
        raise ValueError(f"Text column '{args.text_col}' not found in {args.in_csv}. Columns: {list(df.columns)}")

    texts = df[args.text_col].fillna('').astype(str).tolist()

    vecs = embed_texts(
        texts=texts,
        model_name=args.model,
        pooling=args.pooling,
        batch_size=args.batch_size,
        max_length=args.max_length,
        device=None,
    )

    emb_dim = vecs.shape[1]
    emb_strings = [json.dumps(v.tolist()) for v in vecs]
    df_out = df.copy()
    df_out['embedding'] = emb_strings

    if args.explode:
        emb_cols = [f'emb_{i}' for i in range(emb_dim)]
        emb_df = pd.DataFrame(vecs, columns=emb_cols)
        df_out = pd.concat([df_out.reset_index(drop=True), emb_df.reset_index(drop=True)], axis=1)

    df_out.to_csv(args.out_csv, index=False)
    print(f'Saved embeddings to {args.out_csv}')
    print(f'Embedding dim: {emb_dim}; rows: {len(df_out)}')
    if args.time_col and args.time_col in df_out.columns:
        print(f'Detected timestamp column: {args.time_col}')

if __name__ == '__main__':
    main()