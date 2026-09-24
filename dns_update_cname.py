#!/opt/aws-dyndns/.venv/bin/python
import boto3
import argparse

class AWSDynDns(object):
    def __init__(self, domain, record, hosted_zone_id, profile_name, ttl, instance_id,
                 region_name, instance_profile_name):
        route53_session = boto3.Session(profile_name=profile_name)
        instance_session = boto3.Session(
            profile_name=instance_profile_name,
            region_name=region_name
        )
        self.client = route53_session.client('route53')
        self.ec2_client = instance_session.client('ec2')
        self.domain = domain
        self.record = record
        self.ttl = ttl
        self.hosted_zone_id = hosted_zone_id
        self.instance_id = instance_id
        if self.record:
            self.fqdn = "{0}.{1}".format(self.record, self.domain)
        else:
            self.fqdn = self.domain

    def get_public_dns_name(self):
        try:
            response = self.ec2_client.describe_instances(InstanceIds=[self.instance_id])
            reservations = response.get('Reservations', [])
            instances = [instance for reservation in reservations
                         for instance in reservation.get('Instances', [])]
            if not instances or not instances[0].get('PublicDnsName'):
                raise Exception("instance has no public DNS name")
            self.public_dns_name = instances[0]['PublicDnsName']
            print("Found public DNS name: {0}".format(self.public_dns_name))
        except Exception as error:
            raise Exception("error getting public DNS name: {0}".format(error))

    def get_hosted_zone_id(self):
        try:
            self.hosted_zone_list = self.client.list_hosted_zones_by_name()['HostedZones']
            for zone in self.hosted_zone_list:
                if self.domain in zone['Name']:
                    self.hosted_zone_id = zone['Id'].split('/')[2]
        except Exception:
            raise Exception("error getting hosted zone ID")

    def check_existing_record(self):
        self.get_public_dns_name()

        response = self.client.list_resource_record_sets(
            HostedZoneId=self.hosted_zone_id,
            StartRecordName=self.fqdn,
            StartRecordType='CNAME',
        )

        found_flag = False

        if len(response['ResourceRecordSets']) == 0:
            return found_flag
            #raise Exception("Could not find any records matching domain: {0}".format(self.domain))

        if self.fqdn in response['ResourceRecordSets'][0]['Name']:
            for record in response['ResourceRecordSets'][0]['ResourceRecords']:
                if self.public_dns_name == record['Value']:
                    found_flag = True
        else:
            raise Exception("Cannot find record set for domain: {0}".format(self.fqdn))

        return found_flag

    def update_record(self):
        if not self.hosted_zone_id:
            self.get_hosted_zone_id()

        if self.check_existing_record():
             print("CNAME is already up to date")
        else:
            print("Updating resource record CNAME")
            response = self.client.change_resource_record_sets(
                HostedZoneId=self.hosted_zone_id,
                ChangeBatch={
                    'Comment': 'string',
                    'Changes': [
                        {
                            'Action': 'UPSERT',
                            'ResourceRecordSet': {
                                'Name': self.fqdn,
                                'Type': 'CNAME',
                                'TTL': self.ttl,
                                'ResourceRecords': [
                                    {
                                        'Value': self.public_dns_name
                                    },
                                ],
                            }
                        },
                    ]
                }
            )
            print("Status: {}".format(response['ChangeInfo']['Status']))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage a dynamic home IP address with an AWS hosted route53 domain")

    parser.add_argument(
        "--profile","-p",
        default='ddns',
        help="AWS credential profile for Route 53",
        required=False
    )

    parser.add_argument(
        "--instance-profile",
        default='ec2',
        help="AWS credential profile for EC2 instance lookup",
        required=False
    )

    parser.add_argument(
        "--domain", "-d",
        help="Domain to modify",
        required=True
    )

    parser.add_argument(
        "--record", "-r",
        help="Record to modify",
        required=False
    )

    parser.add_argument(
        "--zone", "-z",
        help="AWS hosted zone id",
        required=False
    )

    parser.add_argument(
        "--ttl",
        default=300,
        help="Record TTL",
        required=False
    )

    parser.add_argument(
        "--instance-id",
        help="EC2 instance ID whose public DNS name should be the CNAME target",
        required=True
    )

    parser.add_argument(
        "--region",
        help="AWS region containing the EC2 instance",
        required=False
    )

    args = parser.parse_args()

    run = AWSDynDns(args.domain, args.record, args.zone, args.profile, args.ttl,
                    args.instance_id, args.region, args.instance_profile)
    run.update_record()
