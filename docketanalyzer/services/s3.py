import os
from contextlib import suppress
from pathlib import Path
from typing import Any

import boto3
from botocore.client import Config

from .. import env


def export_env():
    """Export s3 env for boto3."""
    keys = [
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_S3_BUCKET_NAME",
        "AWS_S3_ENDPOINT_URL",
    ]
    for key in keys:
        if key not in os.environ:
            os.environ[key] = env[key]


class S3:
    """A class for syncing local data with an S3 bucket.

    Attributes:
        data_dir (Path): Local directory for data storage.
        bucket (Path): S3 bucket name.
        endpoint_url (Optional[str]): Custom S3 endpoint URL.
        client (boto3.client): Boto3 S3 client for direct API interactions.
    """

    def __init__(self, data_dir: str | None = None) -> None:
        """Initialize the S3 service.

        Args:
            data_dir (Optional[str]): Path to local data directory.
                If None, uses env.DATA_DIR.
        """
        export_env()
        self.data_dir = Path(data_dir or env.DATA_DIR)
        self.bucket = env.AWS_S3_BUCKET_NAME
        self.endpoint_url = env.AWS_S3_ENDPOINT_URL
        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=env.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=env.AWS_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
        )

    def _sync(
        self,
        from_path: str | Path,
        to_path: str | Path,
        confirm: bool = False,
        exclude_hidden: bool = True,
        exact_timestamps: bool = True,
        **kwargs: Any,
    ) -> None:
        """Execute an AWS S3 sync command between two paths.

        This is a private helper method that constructs and executes an AWS CLI command
        for syncing files between local and S3 storage.

        Args:
            from_path (Union[str, Path]): Source path to sync from.
            to_path (Union[str, Path]): Destination path to sync to.
            confirm (bool): If True, asks for confirmation before executing the command.
            exclude_hidden (bool): If True, excludes hidden files and directories.
            exact_timestamps (bool): If True, compares timestamps.
            **kwargs: Additional arguments to pass to the AWS CLI s3 sync command.
        """
        cmd = f"aws s3 sync {from_path} {to_path}"

        if self.endpoint_url is not None:
            cmd += f" --endpoint-url {self.endpoint_url}"

        if exclude_hidden:
            cmd += ' --exclude "*/.*" --exclude ".*"'

        kwargs["exact_timestamps"] = exact_timestamps
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        for k, v in kwargs.items():
            k = k.replace("_", "-")
            if isinstance(v, bool):
                if v:
                    cmd += f" --{k}"
            elif isinstance(v, list | tuple):
                for item in v:
                    cmd += f' --{k} "{item}"'
            else:
                cmd += f' --{k} "{v}"'

        if confirm:
            print("Run the following command?")
            print(cmd)
            response = input("y/n: ")
            if response == "y":
                os.system(cmd)
        else:
            os.system(cmd)

    def _prepare_paths(
        self,
        path: str | Path | None,
        from_path: str | Path | None,
        to_path: str | Path | None,
    ) -> tuple[Path, Path]:
        """Prepare source and destination paths for sync operations.

        This method handles path normalization and ensures paths are properly
        formatted for sync operations.

        Args:
            path (Optional[Union[str, Path]]): If provided, used as both
                from_path and to_path.
            from_path (Optional[Union[str, Path]]): Source path for sync operation.
            to_path (Optional[Union[str, Path]]): Destination path for sync operation.

        Returns:
            Tuple[Path, Path]: Normalized from_path and to_path.
        """
        if path is not None:
            path = Path(path)

            with suppress(ValueError):
                path = path.relative_to(self.data_dir)
            from_path = to_path = path

        if path is None and from_path is None and to_path is None:
            raise ValueError("Must provide at least one path argument")

        from_path = Path() if from_path is None else Path(from_path)
        to_path = Path() if to_path is None else Path(to_path)

        return from_path, to_path

    def push(
        self,
        path: str | Path | None = None,
        from_path: str | Path | None = None,
        to_path: str | Path | None = None,
        **kwargs: Any,
    ) -> None:
        """Push data from local storage to S3.

        Syncs files from a local directory to an S3 bucket path.

        Args:
            path (Optional[Union[str, Path]]): If provided, used as both
                from_path and to_path.
            from_path (Optional[Union[str, Path]]): Local source path to sync from.
            to_path (Optional[Union[str, Path]]): S3 destination path to sync to.
            **kwargs: Additional arguments to pass to the AWS CLI s3 sync command.
        """
        from_path, to_path = self._prepare_paths(path, from_path, to_path)
        if self.data_dir is not None:
            from_path = self.data_dir / from_path
        to_path = f"s3://{Path(self.bucket) / to_path}"
        self._sync(from_path, to_path, **kwargs)

    def pull(
        self,
        path: str | Path | None = None,
        from_path: str | Path | None = None,
        to_path: str | Path | None = None,
        **kwargs: Any,
    ) -> None:
        """Pull data from S3 to local storage.

        Syncs files from an S3 bucket path to a local directory.

        Args:
            path (Optional[Union[str, Path]]): If provided, used as both
                from_path and to_path.
            from_path (Optional[Union[str, Path]]): S3 source path to sync from.
            to_path (Optional[Union[str, Path]]): Local destination path to sync to.
            **kwargs: Additional arguments to pass to the AWS CLI s3 sync command.
        """
        from_path, to_path = self._prepare_paths(path, from_path, to_path)
        if self.data_dir is not None:
            to_path = self.data_dir / to_path
        from_path = f"s3://{Path(self.bucket) / from_path}"
        self._sync(from_path, to_path, **kwargs)

    def download(self, s3_key: str, local_path: str | Path | None = None) -> Path:
        """Download a single file from S3 using the boto3 client.

        This method downloads a specific file from S3 to a local path.
        If local_path is not provided, it will mirror the S3 path structure
        in the data directory.

        Args:
            s3_key (str): The key of the file in the S3 bucket.
            local_path (Optional[Union[str, Path]]): The local path to save the file to.
                If None, the file will be saved to data_dir/s3_key.

        Returns:
            Path: The path to the downloaded file.

        Raises:
            botocore.exceptions.ClientError: If the download fails.
        """
        local_path = self.data_dir / s3_key if local_path is None else Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        self.client.download_file(
            Bucket=self.bucket, Key=s3_key, Filename=str(local_path)
        )

        return local_path

    def upload(self, local_path: str | Path, s3_key: str | None = None) -> str:
        """Upload a single file to S3 using the boto3 client.

        This method uploads a specific file from a local path to S3.
        If s3_key is not provided, it will use the relative path from data_dir
        as the S3 key.

        Args:
            local_path (Union[str, Path]): The local path of the file to upload.
            s3_key (Optional[str]): The key to use in the S3 bucket.
                If None, the relative path from data_dir will be used.

        Returns:
            str: The S3 key of the uploaded file.

        Raises:
            FileNotFoundError: If the local file does not exist.
            botocore.exceptions.ClientError: If the upload fails.
        """
        local_path = Path(local_path)

        if not local_path.exists():
            raise FileNotFoundError(f"File not found: {local_path}")

        if s3_key is None:
            try:
                s3_key = str(local_path.relative_to(self.data_dir))
            except ValueError:
                s3_key = local_path.name

        self.client.upload_file(
            Filename=str(local_path), Bucket=self.bucket, Key=s3_key
        )

        return s3_key

    def delete(self, s3_key: str) -> None:
        """Delete a single file from S3 using the boto3 client.

        Args:
            s3_key (str): The key of the file in the S3 bucket to delete.

        Raises:
            botocore.exceptions.ClientError: If the deletion fails.
        """
        self.client.delete_object(Bucket=self.bucket, Key=s3_key)

    def status(self) -> bool:
        """Check if S3 connection is working."""
        try:
            self.client.list_buckets()
            return True
        except Exception:
            return False


def load_s3(data_dir: str | Path | None = None) -> S3:
    """Load the S3 service.

    Args:
        data_dir (Optional[Union[str, Path]]): Path to local data directory.
            If None, uses env.DATA_DIR.

    Returns:
        S3: An instance of the S3 class.
    """
    return S3(data_dir)
