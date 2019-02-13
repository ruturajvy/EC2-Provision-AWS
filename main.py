import boto3
import json
ec2 = boto3.client('ec2')
resource = boto3.resource('ec2')


def listimages(ec2):
	response = ec2.describe_images(Filters=[\
	{'Name': 'state', 'Values': ['available']},\
	{'Name':'architecture','Values':['x86_64']},\
	{'Name':'name','Values':['ubuntu/images/hvm-ssd/ubuntu-xenial-16.04-amd64-server-20181223']},])
	for image in response['Images']:
		print("Name: " + image['Name'])
		print("ImageId: " + image['ImageId'])
	return response['Images'][0]['ImageId']

def generate_keypair(ec2, name):
	
	allkeys = ec2.describe_key_pairs()
	#print(allkeys)
	#print([key['KeyName'] for key in allkeys['KeyPairs']])
	if name.lower() in [key['KeyName'].lower() for key in allkeys['KeyPairs']]:
		print("Requested key-pair already exists")

	else:
		ec2key = ec2.create_key_pair(KeyName = name)
		kname = ec2key['KeyName']	
		with open(kname +'.pem','w') as f:
			f.write(ec2key['KeyMaterial'])
		print("Created a key-pair named: %s" % (kname))
		print("Stored the private key in %s.pem" %(kname) )


def create_security_group(ec2,name):
	allgroups = ec2.describe_security_groups()
	if name in [group['GroupName'] for group in allgroups['SecurityGroups']]:
		print("Requested security group already exists")
	else:
		group = ec2.create_security_group(GroupName=name,Description='Created for DevOps HW1')
		groupid = group['GroupId']
		print('Security Group Created %s.' % (groupid))
		data = ec2.authorize_security_group_ingress(
        GroupId=groupid,
        IpPermissions=[
            {'IpProtocol': 'icmp',
             'FromPort': -1,
             'ToPort': -1,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol': 'tcp',
             'FromPort': 22,
             'ToPort': 22,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
        ])
		print('Ingress Successfully Set %s' % data)
		
def create_instance(resource,imageid,instancetype, keyname, group):
	instance = resource.create_instances(\
	MinCount=1,\
	MaxCount=1,\
	ImageId=imageid,\
	InstanceType=instancetype,\
	KeyName=keyname,\
	SecurityGroupIds=[group]\
	)
	print(instance)
	return str(instance[0].instance_id)

def get_instance_info(res,id1):
	print(id1)
	instance = res.describe_instances(InstanceIds=[id1])
	ip = instance['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['Association']['PublicIp']
	#print("%s " %(instance['Reservations'][0]['Instances'][0]['NetworkInterfaces'][0]['Association']['PublicIp']))
	return ip
def terminate_instances(ec2,instance_list):
	response = ec2.terminate_instances(InstanceIds=instance_list)
	prettyprint(response)
#list_regions(ec2)	
#listimages(ec2)
imageid = 'ami-03a935aafa6b52b97'
sec_grp_id = 'sg-03547e18cffebc50a'
ins_id = 'i-0ac7cd288438c28c4'
generate_keypair(ec2, 'DevOps-Key')
#create_security_group(ec2, 'DevOps-Group')
vm_id = create_instance(resource, listimages(ec2), 't2.micro', 'DevOps-Key', sec_grp_id)
print(vm_id)
vm_ip = get_instance_info(ec2,vm_id)
print(vm_ip)

