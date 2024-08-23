import os
from pathlib import Path
from docketanalyzer.utils import DATA_DIR, AWS_S3_BUCKET_NAME, AWS_S3_ENDPOINT_URL


class S3Utility:
    def __init__(
        self, bucket=AWS_S3_BUCKET_NAME,
        endpoint_url=AWS_S3_ENDPOINT_URL,
        data_dir=DATA_DIR,
    ):
        self.bucket = Path(bucket)
        self.data_dir = None if data_dir is None else Path(data_dir)
        self.endpoint_url = endpoint_url

    def _sync(
        self, from_path, to_path, confirm=False,
        exclude_hidden=True, **kwargs
    ):
        cmd = f'aws s3 sync {from_path} {to_path}'

        if self.endpoint_url is not None:
            cmd += f' --endpoint-url {self.endpoint_url}'

        if exclude_hidden:
            cmd += ' --exclude "*/.*" --exclude ".*"'

        for k, v in kwargs.items():
            k = k.replace('_', '-')
            if isinstance(v, bool):
                if v:
                    cmd += f' --{k}'
            elif isinstance(v, (list, tuple)):
                for item in v:
                    cmd += f' --{k} "{item}"'
            else:
                cmd += f' --{k} "{v}"'

        if confirm:
            print('Run the following command?')
            print(cmd)
            response = input('y/n: ')
            if response == 'y':
                os.system(cmd)
        else:
            os.system(cmd)

    def push(self, from_path: str, to_path: str, **kwargs):
        from_path, to_path = Path(from_path), Path(to_path)
        if self.data_dir is not None:
            from_path = self.data_dir / from_path
        to_path = f's3://{self.bucket / to_path}'
        self._sync(from_path, to_path, **kwargs)

    def pull(self, from_path: str, to_path: str, **kwargs):
        from_path, to_path = Path(from_path), Path(to_path)
        if self.data_dir is not None:
            to_path = self.data_dir / to_path
        from_path = f's3://{self.bucket / from_path}'
        self._sync(from_path, to_path, **kwargs)
