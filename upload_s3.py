# This script collects EC2 instance metadata and uploads it to an S3 bucket
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import boto3
from botocore.exceptions import ClientError
import requests
import os

# Collecting information about EC2 instance from AWS service

user_data_url = 'http://169.254.169.254/latest/user-data'
meta_data_url = 'http://169.254.169.254/latest/meta-data'
ec2InsDatafile = 'ec2InsDatafile.txt'

ec2_params = {
    'Instance ID': 'instance-id',
    'Reservation ID': 'reservation-id',
    'Public IP': 'public-ipv4',
    'Private IP': 'local-ipv4',
    'Security Groups': 'security-groups'
}

try:
    with open(ec2InsDatafile, 'w') as fh:
        for param, endpoint in ec2_params.items():
            try:
                response = requests.get(f"{meta_data_url}/{endpoint}")
                response.raise_for_status()  # ensure we catch HTTP errors
                fh.write(f"{param}: {response.text}\n")
            except requests.RequestException as e:
                print(f"Failed to retrieve {param}: {str(e)}")
        
        # Fetching OS-related info
        os_name = os.popen("grep '^NAME' /etc/os-release | cut -d'=' -f2").read().strip()
        os_version = os.popen("grep '^VERSION=' /etc/os-release | cut -d'=' -f2").read().strip()
        users = os.popen("grep -E 'bash|sh' /etc/passwd | awk -F ':' '{print $1}' | xargs echo").read().strip()

        fh.write(f"OS NAME: {os_name}\n")
        fh.write(f"OS VERSION: {os_version}\n")
        fh.write(f"Loginable Users: {users}\n")

except IOError as e:
    print(f"Failed to retrieve {param} from EC2 metadata: {str(e)}")

# Upload file to S3 storage
s3_bucket_name = 'new-bucket-e05ab0e0'
s3 = boto3.client('s3')

try:
    with open(ec2InsDatafile, 'r') as fh:
        instance_id = requests.get(f"{meta_data_url}/instance-id").text.strip()
        s3.put_object(
            Bucket=s3_bucket_name,
            Key=f'system_info_{instance_id}.txt',
            Body=fh.read()
        )
    print(f"File has been uploaded into {s3_bucket_name} S3 bucket with instance_id key.")
except (ClientError, IOError) as e:
    print(f"Failed to upload file to S3: {str(e)}")