import boto
from boto.s3 import connection

#Function taken from AWS and Python Cookbook
def create_bucket(name, region):
    """Creates S3 bucket, location is EU for EU region, US otherwise"""
    s3 = boto.connect_s3()
    bucket = s3.lookup(name)
    if bucket:
        print 'Bucket (%s) already exists' % name
    else:
        try:
            location = connection.Location.DEFAULT
            if region.find('eu') != -1:
                location = connection.Location.EU
            bucket = s3.create_bucket(name, location=location)
        except s3.provider.storage_create_error, e:
            print 'Bucket (%s) is owned by another user' % name
    return bucket

def get_bucket_id(env_id):
    return 'zmicier-env-'+env_id

#Function taken from AWS and Python Cookbook
def store_file(bucket_name, key_name, path_to_file):
    """Write the contents of a local file to S3
    bucket_name The name of the S3 Bucket.
    key_name The name of the object containing the data in S3.
    path_to_file Fully qualified path to local file.
    """
    s3 = boto.connect_s3()
    bucket = s3.lookup(bucket_name)

    # Get a new, blank Key object from the bucket. This Key object only
    # exists locally until we actually store data in it.
    key = bucket.new_key(key_name)

    # Now, overwrite the data with the contents of the file
    key.set_contents_from_filename(path_to_file)
    return key


