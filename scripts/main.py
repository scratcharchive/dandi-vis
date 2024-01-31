import os
import time
from fetch_all_dandisets import fetch_all_dandisets
from dandi_nwb_meta import load_dandi_nwb_meta_output
from d_000582 import d_000582


def main():
    d_000582()


def process_dandisets(*, max_time: float, max_time_per_dandiset: float):
    dandisets = fetch_all_dandisets()

    timer = time.time()
    for dandiset in dandisets:
        print("")
        print(f"Processing {dandiset.dandiset_id} version {dandiset.version}")
        process_dandiset(dandiset.dandiset_id, max_time_per_dandiset)
        elapsed = time.time() - timer
        print(f"Time elapsed: {elapsed} seconds")
        if elapsed > max_time:
            print("Time limit reached.")
            break


def process_dandiset(dandiset_id: str, max_time: float):
    timer = time.time()

    if os.environ.get("AWS_ACCESS_KEY_ID") is not None:
        import boto3

        s3 = boto3.client(
            "s3",
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
            endpoint_url=os.environ["S3_ENDPOINT_URL"],
            region_name="auto",  # for cloudflare
        )
    else:
        s3 = None

    # Load nwb meta output
    print("Loading nwb meta output")
    dandi_nwb_meta_dandiset = load_dandi_nwb_meta_output(dandiset_id)
    if dandi_nwb_meta_dandiset is not None:
        print(f"Loaded {len(dandi_nwb_meta_dandiset.nwb_assets)} assets")
    something_changed = False
    if something_changed:
        print(f"Saving output for {dandiset_id}")
        # _save_output(s3, dandiset_id, X)
    else:
        print(f"Not saving output for {dandiset_id} because nothing changed.")


if __name__ == "__main__":
    main()
