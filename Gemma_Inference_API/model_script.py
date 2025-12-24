from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="google/embeddinggemma-300M",
    local_dir="./models/gemma-300m",
    local_dir_use_symlinks=False
)