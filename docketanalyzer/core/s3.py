import os
from pathlib import Path
from docketanalyzer import env

class S3:
    def __init__(self, bucket=None, endpoint_url=None, data_dir=None):
        self.bucket = Path(bucket or env.AWS_S3_BUCKET_NAME)
        self.data_dir = Path(data_dir or env.DATA_DIR)
        self.endpoint_url = endpoint_url or env.AWS_S3_ENDPOINT_URL


    def _sync(
        self, from_path, to_path, confirm=False,
        exclude_hidden=True, exact_timestamps=True, **kwargs
    ):
        cmd = f'aws s3 sync {from_path} {to_path}'

        if self.endpoint_url is not None:
            cmd += f' --endpoint-url {self.endpoint_url}'

        if exclude_hidden:
            cmd += ' --exclude "*/.*" --exclude ".*"'

        kwargs['exact_timestamps'] = exact_timestamps
        kwargs = {k: v for k,v in kwargs.items() if v is not None}

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

    def prepare_paths(self, path, from_path, to_path):
        if path is not None:
            path = Path(path)
            try:
                path = path.relative_to(self.data_dir)
            except ValueError:
                pass
            from_path = to_path = path
        return Path(from_path), Path(to_path)

    def push(self, path=None, from_path=None, to_path=None, **kwargs):
        from_path, to_path = self.prepare_paths(path, from_path, to_path)
        if self.data_dir is not None:
            from_path = self.data_dir / from_path
        to_path = f's3://{self.bucket / to_path}'
        self._sync(from_path, to_path, **kwargs)

    def pull(self, path=None, from_path=None, to_path=None, **kwargs):
        from_path, to_path = self.prepare_paths(path, from_path, to_path)
        if self.data_dir is not None:
            to_path = self.data_dir / to_path
        from_path = f's3://{self.bucket / from_path}'
        self._sync(from_path, to_path, **kwargs)
