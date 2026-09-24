aws-dyndns
=====

Manage a dynamic home IP address with an AWS hosted route53 domain

# setup

In order to use this tool, you need to set up authentication credentials. Credentials for your AWS account can be found in the [IAM Console](https://console.aws.amazon.com/iam/home). You can create or use an existing user or follow the instructions below to setup a new user.

## IAM policy
Create a [new IAM policy](https://console.aws.amazon.com/iam/home#/policies$new?step=edit) using [ddns_iam_policy.json](ddns_iam_policy.json) as a base. Remember to replace `{YOUR_ZONE_ID_HERE}` with the Hosted Zone ID for the route53 domain you want to update.

Give your policy a meaningful name and description, you'll need to refer to it in the next section.
![IAM_review_policy](screenshots/IAM_review_policy.png)

## IAM user
Create a [new IAM user](https://console.aws.amazon.com/iam/home#/users$new?step=details), give it a user name, and select **Programmatic access** for the access type.
![IAM_add_user](screenshots/IAM_add_user.png)

Next, select **Attach existing policies directly**, find the IAM policy you just created, and click the checkbox to the right of the policy name to attach it to your user.
![IAM_set_permissions](screenshots/IAM_set_permissions.png)

To see your new access key, choose **Show**. Your credentials will look something like this:

    Access key ID: AKIAIOSFODNN7EXAMPLE
    Secret access key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

To download the key pair, choose **Download .csv file**. Store the keys in a secure location.
![IAM_user_accessKey](screenshots/IAM_user_accessKey.png)

## AWS credentials
If you have the AWS CLI installed, then you can use it to configure your credentials file:

    aws configure --profile ddns
Alternatively, you can create the credential file yourself. By default, its location is at ~/.aws/credentials:

    [ddns]
    aws_access_key_id = YOUR_ACCESS_KEY
    aws_secret_access_key = YOUR_SECRET_KEY

By default, `dns_update.py` will use the **ddns** credential profile. You can change this by issuing the `--profile PROFILE` option.

The CNAME updater uses the public DNS name of an EC2 instance as the CNAME target. It uses the `ddns` profile for Route 53 and the `ec2` profile for the instance lookup by default. The EC2 profile requires `ec2:DescribeInstances` permission from [ddns_iam_policy.json](ddns_iam_policy.json). Use `--instance-profile` to select a different EC2 profile.

# usage

## A record

`dns_update.py` updates an A record with the current public IP address:

```
/opt/aws-dyndns/dns_update.py --profile ddns --domain example.com \
        --record home --zone ZONE_ID
```

Options:

* `--profile`, `-p`: AWS credential profile for Route 53. Defaults to `ddns`.
* `--domain`, `-d`: Domain to modify. Required.
* `--record`, `-r`: Record name to modify. Optional.
* `--zone`, `-z`: Route 53 hosted zone ID. If omitted, the domain is used to find it.
* `--ttl`: Record TTL in seconds. Defaults to `300`.

## CNAME record

`dns_update_cname.py` updates a CNAME record to the public DNS name of an EC2 instance:

```
/opt/aws-dyndns/dns_update_cname.py \
        --profile ddns \
        --instance-profile ec2 \
        --region eu-west-1 \
        --domain example.com \
        --record app \
        --instance-id i-0123456789abcdef0 \
        --zone ZONE_ID
```

Options:

* `--profile`, `-p`: AWS credential profile used for Route 53. Defaults to `ddns`.
* `--instance-profile`: AWS credential profile used to query EC2. Defaults to `ec2`.
* `--region`: AWS region containing the EC2 instance. Optional when the instance profile already defines a region.
* `--domain`, `-d`: Domain containing the CNAME record. Required.
* `--record`, `-r`: CNAME record name to modify. Optional.
* `--instance-id`: EC2 instance ID whose public DNS name becomes the CNAME target. Required.
* `--zone`, `-z`: Route 53 hosted zone ID. If omitted, the domain is used to find it.
* `--ttl`: CNAME record TTL in seconds. Defaults to `300`.
