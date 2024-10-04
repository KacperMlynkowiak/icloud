# This script collects EC2 instance metadata and uploads it to an S3 bucket
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import boto3
from botocore.exceptions import ClientError
import requests
import os

# URL to access EC2 instance metadata
meta_data_url = 'http://169.254.169.254/latest/meta-data'

# File where EC2 instance data will be saved
ec2InsDatafile = 'ec2InsDatafile.txt'

# Dictionary to map human-readable labels to EC2 metadata endpoints
ec2_params = {
    'Instance ID': 'instance-id',
    'Public IP': 'public-ipv4',
    'Private IP': 'local-ipv4',
    'Security Groups': 'security-groups'
}

# Try to open the file to write EC2 metadata
try:
    with open(ec2InsDatafile, 'w') as fh:
        # Loop through each EC2 parameter and get its metadata from the endpoint
        for param, endpoint in ec2_params.items():
            try:
                # Fetch metadata from the EC2 instance
                response = requests.get(f"{meta_data_url}/{endpoint}")
                response.raise_for_status()  # Catch any HTTP errors
                fh.write(f"{param}: {response.text}\n")  # Write metadata to file
            except requests.RequestException as e:
                # Print error message if metadata retrieval fails
                print(f"Failed to retrieve {param}: {str(e)}")
        
        # Fetch operating system-related information
        os_name = os.popen("grep '^NAME' /etc/os-release | cut -d'=' -f2").read().strip()
        os_version = os.popen("grep '^VERSION=' /etc/os-release | cut -d'=' -f2").read().strip()
        # Fetch users who can login using bash or sh shell
        users = os.popen("grep -E 'bash|sh' /etc/passwd | awk -F ':' '{print $1}' | xargs echo").read().strip()

        # Write OS name, version, and users to the file
        fh.write(f"OS NAME: {os_name}\n")
        fh.write(f"OS VERSION: {os_version}\n")
        fh.write(f"Loginable Users: {users}\n")

# Catch and handle request errors
except requests.RequestException as e:
    print(f"Failed to retrieve EC2 metadata: {str(e)}")

# Upload the metadata file to the specified S3 bucket
s3_bucket_name = 'applicant-task/r5d4'  # Updated to the correct bucket name
s3 = boto3.client('s3')  # Initialize the S3 client

# Try to upload the metadata file to the specified S3 bucket
try:
    with open(ec2InsDatafile, 'r') as fh:
        # Fetch the EC2 instance ID to use in the S3 object key
        instance_id = requests.get(f"{meta_data_url}/instance-id").text.strip()
        # Upload the file to S3 with the instance ID as part of the file name
        s3.put_object(
            Bucket=s3_bucket_name,
            Key=f'system_info_{instance_id}.txt',
            Body=fh.read()
        )
    # Print success message upon successful upload
    print(f"File has been uploaded into {s3_bucket_name} S3 bucket with instance_id key.")
    
# Catch and handle errors during file upload or S3 operations
except (ClientError, IOError) as e:
    print(f"Failed to upload file to S3: {str(e)}")