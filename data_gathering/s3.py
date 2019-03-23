import json

import boto3


def push_to_s3(local_source, bucket, key):
    s3 = boto3.resource('s3')
    s3.Bucket(bucket).upload_file(local_source, key)


def push_object_to_s3(obj, bucket, key):
    s3 = boto3.client('s3')
    s3.put_object(Body=json.dumps(obj), Bucket=bucket, Key=key)


def pull_from_s3(bucket, key, local_path):
    s3 = boto3.resource('s3')
    s3.Bucket(bucket).download_file(key, local_path)

