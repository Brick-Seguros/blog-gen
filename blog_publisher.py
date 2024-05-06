import boto3

class BlogPublisher:
    def __init__(self, bucket, key, secret, region):
        self.bucket = bucket
        self.key = key
        self.secret = secret
        self.region = region


    def publish(self, title, content: str):

        buffer = content.encode('utf-8')

        session = boto3.Session(
            aws_access_key_id=self.key,
            aws_secret_access_key=self.secret,
            region_name=self.region,
        )

        s3 = session.resource('s3')
        s3.Bucket(self.bucket).put_object(
            Key=title,
            Body=buffer,
            ACL='public-read'
        )
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{title}"



