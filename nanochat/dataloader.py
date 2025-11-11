from collections import deque
import random
import torch

from nanochat.common import get_dist_info
from nanochat.dataset import parquets_iter_batched
from nanochat.tokenizer import get_tokenizer

# Simple helper for mixing in text for a user provided topic into FineWeb batches.
def mixed_iter_batched(split, topic_path, topic_ratio=0.005, start=0, step=1):
    """
    Yields batches of text: mostly from FineWeb parquets, occasionally replaced
    with text lines from the given topic corpus.

    topic_ratio : fraction of batches that should be Topic text (e.g., 0.005 = 0.5%)
    start/step  : for DDP rank sharding (same as parquets_iter_batched)
    """
    # Load Topic corpus lines once
    with open(topic_path, encoding="utf-8") as f:
        topic_lines = [ln.strip() for ln in f if ln.strip()]

    topic_idx = 0
    fine_iter = parquets_iter_batched(split=split, start=start, step=step)

    for fine_batch in fine_iter:
        if random.random() < topic_ratio:
            # build a batch from Topic lines of roughly equal length
            topic_batch = []
            while len(topic_batch) < len(fine_batch):
                topic_batch.append(topic_lines[topic_idx % len(topic_lines)])
                topic_idx += 1
            yield topic_batch
        else:
            yield fine_batch

# Data loader that mixes in a topic_ratio % of topic data into batches.
def tokenizing_distributed_data_loader(
    B,
    T,
    split,
    tokenizer_threads=4,
    tokenizer_batch_size=128,
    device="cuda",
    topic_path=None,
    topic_ratio=0.005,
):
    """
    Stream pretraining text from parquet files (and optionally a Topic corpus),
    tokenize, and yield training batches ready for GPU.
    """
    assert split in ["train", "val"], "split must be 'train' or 'val'"
    ddp, ddp_rank, ddp_local_rank, ddp_world_size = get_dist_info()
    needed_tokens = B * T + 1  # +1 for the target at the last token
    tokenizer = get_tokenizer()
    bos_token = tokenizer.get_bos_token_id()
    token_buffer = deque()

    # --------------------------------------------------------------
    # build our mixed or pure iterator over document batches
    if topic_path:
        data_iter = mixed_iter_batched(
            split=split,
            topic_path=topic_path,
            topic_ratio=topic_ratio,
            start=ddp_rank,
            step=ddp_world_size,
        )
    else:
        data_iter = parquets_iter_batched(
            split=split,
            start=ddp_rank,
            step=ddp_world_size,
        )

    def document_batches():
        while True:
            for batch in data_iter:
                for i in range(0, len(batch), tokenizer_batch_size):
                    yield batch[i : i + tokenizer_batch_size]

    batches = document_batches()
    batch_index = 0

    # --------------------------------------------------------------
    while True:
        # Accumulate enough tokens for one training step
        while len(token_buffer) < needed_tokens:
            doc_batch = next(batches)
            token_lists = tokenizer.encode(
                doc_batch,
                prepend=bos_token,
                num_threads=tokenizer_threads,
            )
            for tokens in token_lists:
                token_buffer.extend(tokens)
            batch_index += 1

        # Slice out the next B*T tokens
        tokens = [token_buffer.popleft() for _ in range(needed_tokens)]
        scratch = torch.tensor(tokens, dtype=torch.int64, pin_memory=(device == "cuda"))
        inputs_cpu = scratch[:-1].to(dtype=torch.int32)
        targets_cpu = scratch[1:]

        # reshape and move to GPU
        inputs = inputs_cpu.view(B, T).to(device=device, dtype=torch.int32, non_blocking=True)
        targets = targets_cpu.view(B, T).to(device=device, dtype=torch.int64, non_blocking=True)
        yield inputs, targets
